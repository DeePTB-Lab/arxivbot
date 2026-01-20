import arxiv
from typing import List, Optional
from ..config import ArxivConfig
from .models import Paper
from loguru import logger

class ArxivFetcher:
    def __init__(self, config: ArxivConfig):
        self.config = config
        self.client = arxiv.Client()

    def get_latest_papers(self, max_results: int = 100) -> List[Paper]:
        all_papers = []
        for category in self.config.category_list:
            logger.info(f"Fetching latest papers from arXiv category: {category}")
            search_query = f'cat:{category}'
            search = arxiv.Search(
                query=search_query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.SubmittedDate
            )
            
            for result in self.client.results(search):
                # Remove the version number from the id
                paper_id = result.get_short_id()
                version_pos = paper_id.find('v')
                if version_pos != -1:
                    paper_id = paper_id[:version_pos]

                paper = Paper(
                    title=result.title,
                    id=paper_id,
                    abstract=result.summary.replace('\n', ' '),
                    url=result.entry_id,
                    published=result.published.date().isoformat()
                )
                all_papers.append(paper)
        
        return self._deduplicate(all_papers)

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
            # Check if any keyword matches words in abstract
            # Simple word matching as in original code
            abstract_words = set(paper.abstract.lower().split())
            if keywords & abstract_words:
                results.append(paper)
        
        logger.info(f"Keyword filtering kept {len(results)} papers.")
        return results
