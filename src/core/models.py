from typing import Dict, List, Optional
from pydantic import BaseModel

class Paper(BaseModel):
    id: str
    title: str
    abstract: str
    url: str
    published: str
    zh_abstract: Optional[str] = None
    introduction: Optional[str] = None
    conclusion: Optional[str] = None
    deep_summary: Optional[str] = None
    conclusion: Optional[str] = None
    
    def get_short_id(self) -> str:
        version_pos = self.id.find('v')
        if version_pos != -1:
            return self.id[:version_pos]
        return self.id

class ProcessedPaper(Paper):
    pass
