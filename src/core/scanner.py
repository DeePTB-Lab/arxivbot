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
                try:
                    result = next(client.results(search))
                except StopIteration:
                    logger.error(f"Arxiv ID {arxiv_id} not found.")
                    return None, None
                
                logger.info(f"Downloading source for {arxiv_id}...")
                try:
                    tar_path = result.download_source(dirpath=tmpdirname)
                    logger.info(f"Source downloaded to {tar_path}")
                except Exception as e:
                    logger.warning(f"Failed to download source for {arxiv_id}: {e}")
                    return None, None
                
                # Extract
                if not tarfile.is_tarfile(tar_path):
                    logger.warning(f"{arxiv_id} source is not a tarfile (maybe PDF only).")
                    return None, None
                
                try:
                    with tarfile.open(tar_path) as tar:
                        tar.extractall(path=tmpdirname)
                        logger.info(f"Extracted tarball to {tmpdirname}")
                except Exception as e:
                    logger.error(f"Failed to extract tarball: {e}")
                    return None, None
                
                # Find main .tex file (Recursive)
                tex_files = []
                for root, dirs, files in os.walk(tmpdirname):
                    for file in files:
                        if file.endswith('.tex'):
                            tex_files.append(os.path.join(root, file))
                
                if not tex_files:
                    logger.warning(f"No .tex files found in source for {arxiv_id}.")
                    return None, None
                
                logger.info(f"Found {len(tex_files)} .tex files used for scanning.")

                # Simple heuristic: largest tex file or one with \begin{document}
                main_tex_content = ""
                
                # Sort files for determinism
                tex_files.sort()

                candidate_files = []
                
                # Pass 1: Find all files with \begin{document}
                for tex_file in tex_files:
                    try:
                        with open(tex_file, 'r', errors='ignore') as f:
                            content = f.read()
                            if "\\begin{document}" in content:
                                candidate_files.append((tex_file, content))
                    except Exception as e:
                        logger.warning(f"Error reading {tex_file}: {e}")
                        continue
                
                logger.info(f"Found {len(candidate_files)} candidate files with \\begin{{document}}.")

                # Pass 2: Select the best candidate
                # Priority: Contains "\section{Introduction}" -> Largest size
                best_candidate_content = None
                
                for fname, content in candidate_files:
                    # Check for Introduction (roughly)
                    if re.search(r'\\section\{{\s*Introduction', content, re.IGNORECASE):
                        logger.info(f"Selected {os.path.basename(fname)} (contains Introduction).")
                        best_candidate_content = content
                        break
                
                # Fallback: If no Introduction found, pick the largest candidate (likely the main paper)
                if not best_candidate_content and candidate_files:
                    # Sort by length of content (proxy for file size)
                    candidate_files.sort(key=lambda x: len(x[1]), reverse=True)
                    best_candidate_content = candidate_files[0][1]
                    logger.info(f"Selected {os.path.basename(candidate_files[0][0])} by size (fallback).")

                # Fallback 2: If no \\begin{document} found at all, try largest .tex file
                if not best_candidate_content and tex_files:
                    try:
                        largest_file = max(tex_files, key=os.path.getsize)
                        logger.info(f"No \\begin{{document}} found, using largest file: {os.path.basename(largest_file)}")
                        with open(largest_file, 'r', errors='ignore') as f:
                            best_candidate_content = f.read()
                    except Exception as e:
                        logger.error(f"Error reading largest file: {e}")

                if not best_candidate_content:
                    logger.warning("Could not identify main .tex content.")
                    return None, None
                
                main_tex_content = best_candidate_content

                # Regex extraction (Simplified)
                # Remove comments
                main_tex_content = re.sub(r'%.*', '', main_tex_content)
                
                intro = self._find_section(main_tex_content, "Introduction")
                conclusion = self._find_section(main_tex_content, "Conclusion")
                
                if not intro and not conclusion:
                    logger.warning(f"Deep scan extraction failed: No Intro/Conclusion found in {arxiv_id}")
                else:
                    logger.info(f"Deep scan success: Intro({len(intro) if intro else 0} chars), Conc({len(conclusion) if conclusion else 0} chars)")
                
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
