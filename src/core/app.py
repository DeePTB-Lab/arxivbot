import os
import json
from loguru import logger
from ..config import Settings
from .fetcher import ArxivFetcher
from .processor import PaperProcessor
from .notifier import LarkNotifier, EmailNotifier
from .scanner import ArxivContentScanner
from .models import Paper

# Determine the absolute path to the project root
# This file is in src/core/app.py -> .../src/core/app.py
# Root is .../ (3 levels up)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))

class ArxivBot:
    def __init__(self, 
                 config_path: str = None, 
                 papers_file: str = None, 
                 hunt_file: str = None,
                 paper_config_path: str = None,
                 # CLI Overrides
                 use_llm: bool = False,
                 enable_deep_scan: bool = False):
        
        self.config_path = config_path or os.path.join(PROJECT_ROOT, "data", "config.yaml")
        self.paper_config_path = paper_config_path or os.path.join(PROJECT_ROOT, "data", "paper.yaml")
        self.papers_file = papers_file or os.path.join(PROJECT_ROOT, "data", "paper_history.json")
        self.hunt_file = hunt_file or os.path.join(PROJECT_ROOT, "data", "hunt_prompt.md")
        
        self.settings = Settings.load_from_yaml(self.config_path, self.paper_config_path)
        
        # Apply CLI overrides (Store True strategy: If True, overwrite. If False... wait, user said "without means close")
        # If the user runs `axvbot` (without flags), use_llm is False.
        # This implies we force these settings to False if the flag is missing?
        # "without --use_llm means close". So yes, we strictly follow the flag value.
        
        self.settings.arxiv.use_llm_for_filtering = use_llm
        self.settings.arxiv.use_llm_for_translation = use_llm
        self.settings.arxiv.enable_deep_scan = enable_deep_scan

    def load_processed_ids(self) -> set:
        if os.path.exists(self.papers_file):
            try:
                with open(self.papers_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return set(d['id'] for d in data)
            except Exception:
                return set()
        return set()

    def save_papers(self, papers: list):
        current_data = []
        if os.path.exists(self.papers_file):
            try:
                with open(self.papers_file, 'r', encoding='utf-8') as f:
                    current_data = json.load(f)
            except Exception:
                current_data = []
        
        new_data = [p.model_dump() for p in papers]
        combined = new_data + current_data
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.papers_file), exist_ok=True)
        
        with open(self.papers_file, 'w', encoding='utf-8') as f:
            json.dump(combined, f, indent=4, ensure_ascii=False)

    def run(self):
        # 1. Fetch Papers
        fetcher = ArxivFetcher(self.settings.arxiv)
        papers = fetcher.get_latest_papers()
        
        # 2. Filter by Keywords
        papers = fetcher.filter_by_keywords(papers)
        
        # 3. Filter by LLM
        if self.settings.arxiv.use_llm_for_filtering:
            hunt_prompt = ""
            if os.path.exists(self.hunt_file):
                with open(self.hunt_file, 'r', encoding='utf-8') as f:
                    hunt_prompt = f.read()
            
            if hunt_prompt:
                processor = PaperProcessor(self.settings.llm)
                papers = processor.filter_papers_by_llm(papers, hunt_prompt)

        # 4. Deduplicate against history
        processed_ids = self.load_processed_ids()
        new_papers = [p for p in papers if p.id not in processed_ids]
        logger.info(f"Process kept {len(new_papers)} new papers after history check.")

        if not new_papers:
            logger.info("No new papers to process.")
            return

        # 5. Deep Scan (Optional)
        if self.settings.arxiv.enable_deep_scan:
            scanner = ArxivContentScanner()
            for paper in new_papers:
                scanner.scan_paper(paper)
            
            # Generate Deep Summary after scanning
            if self.settings.arxiv.use_llm_for_filtering: # Assuming we use the same LLM config/flag
                processor = PaperProcessor(self.settings.llm)
                new_papers = processor.generate_deep_summary(new_papers)

        # 6. Translate Abstracts
        if self.settings.arxiv.use_llm_for_translation:
            processor = PaperProcessor(self.settings.llm)
            new_papers = processor.translate_abstracts(new_papers)

        # 7. Notify (Lark + Email)
        if self.settings.lark:
            lark_notifier = LarkNotifier(self.settings.lark)
            lark_notifier.post(new_papers, self.settings.arxiv.tag)
        
        if self.settings.email:
            email_notifier = EmailNotifier(self.settings.email)
            email_notifier.post(new_papers, self.settings.arxiv.tag)

        # 8. Save History
        self.save_papers(new_papers)
        logger.info("Done.")
