import arxiv
from typing import List, Optional
import time
import random
from ..config import ArxivConfig
from .models import Paper
from loguru import logger


class ArxivFetcher:
    def __init__(self, config: ArxivConfig):
        self.config = config
        # Be polite to arXiv: longer delay + more retries than the library defaults
        # (3s / 3) to avoid triggering HTTP 429 rate limits.
        self.client = arxiv.Client(delay_seconds=5.0, num_retries=5)

    def get_latest_papers(self, max_results: int = 100) -> List[Paper]:
        all_papers = []
        for category in self.config.category_list:
            papers = self._fetch_category_with_retry(category, max_results)
            all_papers.extend(papers)

        return self._deduplicate(all_papers)

    def _fetch_category_with_retry(
        self, category: str, max_results: int, max_outer_retries: int = 4
    ) -> List[Paper]:
        """Fetch a single category with exponential backoff on arXiv errors.

        arXiv intermittently returns HTTP 503 (service unavailable) and 429
        (rate limited). The arxiv.Client retries are tightly packed and the
        library raises arxiv.HTTPError when exhausted. We wrap the call with
        exponential backoff + jitter so transient outages do not fail the run.
        """
        search = arxiv.Search(
            query=f"cat:{category}",
            max_results=max_results,
            sort_by=arxiv.SortCriterion.SubmittedDate,
        )
        last_err = None
        for attempt in range(max_outer_retries):
            try:
                label = f"(attempt {attempt + 1}/{max_outer_retries})" if attempt else ""
                logger.info(
                    f"Fetching latest papers from arXiv category: {category} {label}"
                )
                results = []
                for result in self.client.results(search):
                    paper_id = result.get_short_id()
                    version_pos = paper_id.find("v")
                    if version_pos != -1:
                        paper_id = paper_id[:version_pos]
                    results.append(Paper(
                        title=result.title,
                        id=paper_id,
                        abstract=result.summary.replace("\n", " "),
                        url=result.entry_id,
                        published=result.published.date().isoformat(),
                    ))
                return results
            except arxiv.HTTPError as err:
                last_err = err
                status = err.status if hasattr(err, "status") else 0
                if status == 429:
                    base_delay = 30
                elif status == 503:
                    base_delay = 10
                else:
                    base_delay = 5
                delay = base_delay * (2 ** attempt) + random.uniform(0, 3)
                logger.warning(
                    f"arXiv error for {category} (status={status}, attempt "
                    f"{attempt + 1}/{max_outer_retries}): {err}. "
                    f"Retrying in {delay:.1f}s."
                )
                if attempt < max_outer_retries - 1:
                    time.sleep(delay)

        logger.error(
            f"All retries exhausted for category {category}: {last_err}. "
            f"Skipping this category."
        )
        return []

    def _deduplicate(self, papers: List[Paper]) -> List[Paper]:
        seen_ids = set()
        deduplicated = []
        for p in papers:
            if p.id not in seen_ids:
                seen_ids.add(p.id)
                deduplicated.append(p)
        logger.info(f"Fetched {len(deduplicated)} unique papers.")
        return deduplicated

    def filter_by_keywords(self, papers: List[Paper]) -> List[Paper]:
        if not self.config.keyword_list:
            return papers

        logger.info(f"Filtering {len(papers)} papers by keywords...")
        keywords = set(k.lower() for k in self.config.keyword_list)
        results = []
        for paper in papers:
            abstract_words = set(paper.abstract.lower().split())
            if keywords & abstract_words:
                results.append(paper)

        logger.info(f"Keyword filtering kept {len(results)} papers.")
        return results
