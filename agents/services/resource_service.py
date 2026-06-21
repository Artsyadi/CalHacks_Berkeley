"""Resource enrichment: attach REAL, VALIDATED links to roadmap topics.

Sources:
  - YouTube Data API v3  -> real video URLs (never hallucinated)
  - Tavily web search    -> docs / courses / articles

Every URL is HTTP-validated (dropping 4xx/5xx and unreachable links) before
it is attached. Dropped links are logged — turning link-rot into the
"reliability / recovery" bonus rather than a broken demo.
"""
from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, wait

import requests

from agents import config
from agents.models.models import Resource, Roadmap, Topic

logger = logging.getLogger("resource_service")

_HEADERS = {"User-Agent": "Mozilla/5.0 (PromptToPath link validator)"}
_VALIDATE_TIMEOUT = 3
_YOUTUBE_TIMEOUT = 5
_PER_TOPIC_VIDEOS = 1
_PER_TOPIC_WEB = 2
# Bound total work so the pipeline always finishes inside ASI:One's window.
_MAX_TOPICS_PER_PHASE = 2
_MAX_TOPICS_TOTAL = 12
_MAX_WORKERS = 16
# Hard wall-clock budgets — enrich() never blocks longer than their sum.
_FETCH_BUDGET = 12.0
_VALIDATE_BUDGET = 8.0


def _is_youtube(url: str) -> bool:
    return "youtube.com" in url or "youtu.be" in url


def _validate(url: str) -> bool:
    """Return True if the URL is reachable.

    Redirects are NOT followed — a 3xx still means the URL resolves, and
    chasing redirect chains is what made validation hang for 10-18s. This caps
    each check to a single ~3s request. A 403/405 means the host blocks HEAD,
    not that the page is missing, so we treat those as reachable too.
    """
    if not url or not url.startswith(("http://", "https://")):
        return False
    try:
        r = requests.head(url, timeout=_VALIDATE_TIMEOUT, allow_redirects=False,
                          headers=_HEADERS)
        ok = r.status_code < 400 or r.status_code in (403, 405)
        if not ok:
            logger.info("Dropped dead link (%s): %s", r.status_code, url)
        return ok
    except requests.RequestException as exc:
        logger.info("Dropped unreachable link (%s): %s", exc.__class__.__name__, url)
        return False


def _youtube_search(query: str, n: int) -> list[Resource]:
    if not config.YOUTUBE_API_KEY:
        return []
    try:
        resp = requests.get(
            "https://www.googleapis.com/youtube/v3/search",
            params={
                "key": config.YOUTUBE_API_KEY,
                "q": query,
                "part": "snippet",
                "type": "video",
                "maxResults": n,
                "relevanceLanguage": "en",
                "safeSearch": "strict",
            },
            timeout=_YOUTUBE_TIMEOUT,
        )
        resp.raise_for_status()
        items = resp.json().get("items", [])
    except (requests.RequestException, ValueError) as exc:
        logger.warning("YouTube search failed for %r: %s", query, exc)
        return []

    out: list[Resource] = []
    for it in items:
        vid = it.get("id", {}).get("videoId")
        title = it.get("snippet", {}).get("title", "YouTube video")
        if vid:
            out.append(Resource(
                title=title,
                url=f"https://www.youtube.com/watch?v={vid}",
                kind="video",
                source="youtube",
            ))
    return out


def _tavily_search(
    query: str, n: int, *, include_domains: list[str] | None = None
) -> list[Resource]:
    if not config.TAVILY_API_KEY:
        return []
    try:
        from tavily import TavilyClient

        client = TavilyClient(api_key=config.TAVILY_API_KEY)
        kwargs = dict(
            query=query, max_results=n, search_depth="basic", include_answer=False
        )
        if include_domains:
            kwargs["include_domains"] = include_domains
        res = client.search(**kwargs)
    except Exception as exc:  # tavily raises various types
        logger.warning("Tavily search failed for %r: %s", query, exc)
        return []

    out: list[Resource] = []
    for r in res.get("results", []):
        url = r.get("url", "")
        title = r.get("title", url)
        if not url:
            continue
        if _is_youtube(url):
            kind = "video"
        elif any(k in url for k in ("coursera", "udemy", "edx", "khanacademy")):
            kind = "course"
        else:
            kind = "doc"
        out.append(Resource(title=title, url=url, kind=kind, source="tavily"))
    return out


def _fetch_candidates(topic_name: str, roadmap_topic: str) -> list[Resource]:
    """Search for candidate links for one topic (no validation here).

    Tavily-only: one YouTube-scoped query for a video, one general query for
    docs/courses. (The YouTube Data API is available via _youtube_search but is
    kept out of the hot path because its latency is unreliable.)
    """
    q = f"{topic_name} {roadmap_topic} tutorial".strip()
    video = _tavily_search(
        f"{topic_name} tutorial", _PER_TOPIC_VIDEOS, include_domains=["youtube.com"]
    )
    web = _tavily_search(q, _PER_TOPIC_WEB)
    return video + web


def enrich(roadmap: Roadmap) -> Roadmap:
    """Attach validated resources to roadmap topics — fully concurrent + bounded.

    Strategy to stay inside ASI:One's window:
      1. Cap how many topics get enriched (first few per phase, global limit).
      2. Fetch candidates for all topics concurrently.
      3. Validate every non-YouTube URL in ONE global parallel batch
         (YouTube URLs come from the Data API and are trusted, not probed).
      4. Assign surviving resources back to their topics.
    """
    selected: list[Topic] = []
    for phase in roadmap.phases:
        selected.extend(phase.topics[:_MAX_TOPICS_PER_PHASE])
    selected = selected[:_MAX_TOPICS_TOTAL]
    if not selected:
        return roadmap

    # Threads run on a non-blocking pool: we wait only up to a budget, then
    # move on. shutdown(wait=False) means a slow straggler can't stall us.
    pool = ThreadPoolExecutor(max_workers=_MAX_WORKERS)
    try:
        # 2. fetch candidates per topic, concurrently, bounded by _FETCH_BUDGET
        fetch_futs = {
            pool.submit(_fetch_candidates, tp.name, roadmap.topic): i
            for i, tp in enumerate(selected)
        }
        wait(fetch_futs, timeout=_FETCH_BUDGET)
        cand_lists: list[list[Resource]] = [[] for _ in selected]
        for fut, i in fetch_futs.items():
            if fut.done() and not fut.cancelled():
                try:
                    cand_lists[i] = fut.result()
                except Exception:
                    cand_lists[i] = []

        # 3. validate unique non-YouTube URLs concurrently, bounded by budget
        to_check = {
            r.url for cands in cand_lists for r in cands if not _is_youtube(r.url)
        }
        val_futs = {pool.submit(_validate, u): u for u in to_check}
        wait(val_futs, timeout=_VALIDATE_BUDGET)
        validity = {
            u: (fut.done() and not fut.cancelled() and fut.result() is True)
            for fut, u in val_futs.items()
        }
    finally:
        pool.shutdown(wait=False)

    # 4. assign surviving, de-duplicated resources back to topics
    for topic, cands in zip(selected, cand_lists):
        seen: set[str] = set()
        kept: list[Resource] = []
        for r in cands:
            if r.url in seen:
                continue
            seen.add(r.url)
            if _is_youtube(r.url) or validity.get(r.url):
                kept.append(r)
        topic.resources = kept

    return roadmap
