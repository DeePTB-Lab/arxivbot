import os
import tarfile
import re
import tempfile
import shutil
import arxiv
from loguru import logger
from typing import Optional, Tuple
from .models import Paper

class ArxivContentScanner:
    def __init__(self):
        pass

    def scan_paper(self, paper: Paper) -> Paper:
        logger.info(f"Deep scanning paper: {paper.id}...")
        intro, conclusion = self._extract_content(paper.id)
        if intro:
            paper.introduction = intro
        if conclusion:
            paper.conclusion = conclusion
        return paper

    def _extract_content(self, arxiv_id: str) -> Tuple[Optional[str], Optional[str]]:
        try:
            # Create a temporary directory
            with tempfile.TemporaryDirectory() as tmpdirname:
                # Use arxiv client to download source
                client = arxiv.Client()
                # Must search to get the result object to download
                search = arxiv.Search(id_list=[arxiv_id])
                result = next(client.results(search))
                
                # Download tarball
                tar_path = result.download_source(dirpath=tmpdirname)
                
                # Extract
                if not tarfile.is_tarfile(tar_path):
                    logger.warning(f"{arxiv_id} source is not a tarfile (maybe PDF only).")
                    return None, None
                
                with tarfile.open(tar_path) as tar:
                    tar.extractall(path=tmpdirname)
                
                # Find main .tex file
                tex_files = [f for f in os.listdir(tmpdirname) if f.endswith('.tex')]
                if not tex_files:
                    return None, None
                
                # Simple heuristic: largest tex file or one with \begin{document}
                main_tex_content = ""
                for tex_file in tex_files:
                    with open(os.path.join(tmpdirname, tex_file), 'r', errors='ignore') as f:
                        content = f.read()
                        if "\\begin{document}" in content:
                            main_tex_content = content
                            break
                
                if not main_tex_content and tex_files:
                     with open(os.path.join(tmpdirname, tex_files[0]), 'r', errors='ignore') as f:
                        main_tex_content = f.read()

                if not main_tex_content:
                    return None, None

                # Regex extraction (Simplified)
                # Remove comments
                main_tex_content = re.sub(r'%.*', '', main_tex_content)
                
                intro = self._find_section(main_tex_content, "Introduction")
                conclusion = self._find_section(main_tex_content, "Conclusion")
                
                return intro, conclusion

        except Exception as e:
            logger.error(f"Error deep scanning {arxiv_id}: {e}")
            return None, None

    def _find_section(self, content: str, section_name: str) -> Optional[str]:
        # Match \section{Introduction} ... until next \section
        pattern = re.compile(
            rf'\\section\{{\s*{section_name}\s*\}}(.+?)(\\section|\\bibliographystyle|\\end\{{document\}})', 
            re.DOTALL | re.IGNORECASE
        )
        match = pattern.search(content)
        if match:
            text = match.group(1).strip()
            # Cleanup LaTeX commands roughly
            text = re.sub(r'\\[a-zA-Z]+\{.*?\}', '', text) # remove \cmd{arg}
            text = re.sub(r'\\[a-zA-Z]+', '', text) # remove \cmd
            return text[:2000] # Truncate to avoid exploding context
        return None
