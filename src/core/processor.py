from typing import List, Optional
import re
from openai import OpenAI
from ..config import LLMConfig
from .models import Paper
from loguru import logger

class PaperProcessor:
    def __init__(self, config: LLMConfig):
        self.config = config
        self.client = OpenAI(
            api_key=config.api_key,
            base_url=config.base_url
        )

    def _get_llm_response(self, prompt: str) -> Optional[str]:
        try:
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=[{'role': 'user', 'content': prompt}],
                stream=False
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"LLM Server Error: {e}")
            return None

    def filter_papers_by_llm(self, papers: List[Paper], hunt_prompt: str) -> List[Paper]:
        results = []
        logger.info(f"Filtering {len(papers)} papers using LLM...")
        
        for paper in papers:
            prompt = (
                f'你是一个专业的学术论文筛选助手。你的任务是判断给定的论文是否符合我正在寻找的研究内容。\n\n'
                f'请仔细阅读以下论文的标题和摘要：\n标题：{paper.title}\n摘要：{paper.abstract}\n\n'
                f'我正在寻找的研究内容(paper_to_hunt)：\n{hunt_prompt}\n\n---\n\n'
                f'请分析这篇论文的内容是否与我寻找的研究内容相符。在分析时，请考虑：\n'
                f'1. 研究主题的相关性\n2. 论文的关键概念与我的研究描述的匹配程度\n\n'
                f'基于你的分析，如果这篇论文符合我要找的研究内容，请只回答"Yes"；如果不符合，请只回答"No"。'
            )
            
            response = self._get_llm_response(prompt)
            
            if not response:
                logger.warning(f"LLM Error for {paper.title}. Assuming match.")
                results.append(paper)
                continue

            # Remove thinking blocks
            response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL).strip()
            
            if 'yes' in response.lower():
                results.append(paper)
        
        logger.info(f"LLM filtering kept {len(results)} papers.")
        return results

    def translate_abstracts(self, papers: List[Paper]) -> List[Paper]:
        logger.info("Translating abstracts...")
        for paper in papers:
            prompt = (
                f'请将下面的学术论文摘要翻译为中文：\n{paper.abstract}\n\n**注意**：\n'
                f'- 中文语境中常用的英文学术术语可以保留英文原文，如：自然语言处理中的 Transformer 可以保留英文。\n'
                f'- 其他关键的学术术语可以中英文对照，如：后门攻击(Backdoor Attack)。\n'
                f'- 直接给出翻译结果，不需要进行解释，不需要任何其他内容。'
            )
            
            translation = self._get_llm_response(prompt)
            if translation:
                translation = re.sub(r'<think>.*?</think>', '', translation, flags=re.DOTALL).strip()
                paper.zh_abstract = translation
                
        return papers

    def generate_deep_summary(self, papers: List[Paper]) -> List[Paper]:
        logger.info("Generating deep summaries for scanned papers...")
        for paper in papers:
            # Only process papers that have at least some deep scan content
            if not paper.introduction and not paper.conclusion:
                continue

            prompt = f"""
            You are an expert researcher in this field. Please provide a **critical and deep analysis** of the following paper based on its title, abstract, introduction, and conclusion. 
            
            **Do NOT just summarize the paper.** Instead, analyze it like a senior scientist reviewing a colleague's work.
            
            **Output Format (in Chinese):**
            Please use the following plain text format (do NOT use Markdown like ** or *):
            
            1. 核心创新: One concise sentence pinpointing the most novel contribution.
            2. 关键结论: (1) Point 1; (2) Point 2 ...  no need to use bullet points, just use semicolon to separate different points.
            3. 专家点评: A short paragraph (2-3 sentences) evaluating the significance, potential impact, or limitations of this work.

            **Content to Analyze:**
            Title: {paper.title}
            Abstract: {paper.abstract}
            Introduction: {paper.introduction[:2000] if paper.introduction else "None"}...
            Conclusion: {paper.conclusion[:1000] if paper.conclusion else "None"}...
            """
            
            summary = self._get_llm_response(prompt)
            if summary:
                # Clean up thoughts if present
                summary = re.sub(r'<think>.*?</think>', '', summary, flags=re.DOTALL).strip()
                paper.deep_summary = summary
                
        return papers
