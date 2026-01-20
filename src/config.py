from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr
from pydantic_settings import BaseSettings, SettingsConfigDict
import yaml
import os

class LLMConfig(BaseModel):
    model: str = "deepseek-r1:32b"
    base_url: str = "http://localhost:11434/v1"
    api_key: str = "ollama"

class LarkConfig(BaseModel):
    webhook_url: str = Field(..., description="Feishu(Lark) Bot Webhook URL")
    template_id: str = Field(..., description="Card Template ID")
    template_version: str = "1.0.0"

class EmailConfig(BaseModel):
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    sender_email: EmailStr
    sender_password: str
    receiver_email: EmailStr

class ArxivConfig(BaseModel):
    tag: str = "LLM Security"
    category_list: List[str] = ["cs.CL", "cs.AI", "cs.CV", "cs.CR", "cs.LG"]
    keyword_list: List[str] = []
    use_llm_for_filtering: bool = True
    use_llm_for_translation: bool = True
    enable_deep_scan: bool = False

class Settings(BaseSettings):
    lark: Optional[LarkConfig] = None
    email: Optional[EmailConfig] = None
    arxiv: ArxivConfig
    llm: LLMConfig

    model_config = SettingsConfigDict(
        env_nested_delimiter='__',
        env_prefix='ARXIV_',
        extra='ignore'
    )

    @classmethod
    def load_from_yaml(cls, path: str = "config.yaml", paper_config_path: str = None) -> "Settings":
        raw_config = {}
        
        # 1. Load Main Config (Private Secrets)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                raw_config = yaml.safe_load(f) or {}
                
        # 2. Load Paper Config (Public Keywords) -> Merge into raw_config
        # Notes: Paper config values will override main config if present, 
        # but realistically they should be separate.
        if paper_config_path and os.path.exists(paper_config_path):
             with open(paper_config_path, "r", encoding="utf-8") as f:
                paper_data = yaml.safe_load(f) or {}
                # Update raw_config with paper_data (Paper Config has precedence for paper settings)
                raw_config.update(paper_data)

        # If neither file exists, we rely on Env Vars (GitHub Actions case)
        if not raw_config and not os.path.exists(path) and not (paper_config_path and os.path.exists(paper_config_path)):
            return cls()

        # Construct nested dicts from flat-ish yaml if present
        lark_data = None
        if raw_config.get("webhook_url"):
            lark_data = {
                "webhook_url": raw_config.get("webhook_url"),
                "template_id": raw_config.get("template_id"),
                "template_version": raw_config.get("template_version", "1.0.0")
            }
        
        email_data = None
        if raw_config.get("sender_email"):
            email_data = {
                "sender_email": raw_config.get("sender_email"),
                "sender_password": raw_config.get("sender_password"),
                "receiver_email": raw_config.get("receiver_email"),
                "smtp_server": raw_config.get("smtp_server", "smtp.gmail.com"),
                "smtp_port": raw_config.get("smtp_port", 587)
            }
        
        arxiv_data = {
            "tag": raw_config.get("tag"),
            "category_list": raw_config.get("category_list"),
            "keyword_list": raw_config.get("keyword_list"),
            "use_llm_for_filtering": raw_config.get("use_llm_for_filtering"),
            "use_llm_for_translation": raw_config.get("use_llm_for_translation"),
            "enable_deep_scan": raw_config.get("enable_deep_scan")
        }
        
        llm_data = {
            "model": raw_config.get("model"),
            "base_url": raw_config.get("base_url"),
            "api_key": raw_config.get("api_key"),
        }

        # Filter out None values to let Pydantic handle validation/defaults
        arxiv_data = {k: v for k, v in arxiv_data.items() if v is not None}
        llm_data = {k: v for k, v in llm_data.items() if v is not None}

        # For optional sections, we only pass them if we have data or if they will be filled by Env Vars
        # Pydantic Settings will merge arguments with Env Vars. 
        # So we should pass what we have from YAML.
        
        settings_kwargs = {}
        
        # Only pass explicit objects if we actually extracted data from YAML.
        # Otherwise, let BaseSettings load from Environment Variables.
        if lark_data:
            settings_kwargs['lark'] = LarkConfig(**lark_data)
            
        if email_data:
            settings_kwargs['email'] = EmailConfig(**email_data)
            
        if llm_data:
            settings_kwargs['llm'] = LLMConfig(**llm_data)
            
        # Arxiv data is likely present from paper.yaml, but we treat it similarly
        if arxiv_data:
            settings_kwargs['arxiv'] = ArxivConfig(**arxiv_data)

        # Helper: Clean up empty env vars or partial config to avoid pydantic validation error
        # 1. Remove empty values
        for key in list(os.environ.keys()):
             # If env var is empty string, remove it (GitHub Actions case for empty secrets)
             if key.startswith("ARXIV_") and not os.environ[key].strip():
                 del os.environ[key]

        # 2. If SENDER_EMAIL is missing (meaning user didn't config email), 
        #    we must remove ALL ARXIV_EMAIL__ vars (like SMTP_SERVER which might be hardcoded in workflow)
        #    to prevent Pydantic from trying to instantiate partial EmailConfig.
        if "ARXIV_EMAIL__SENDER_EMAIL" not in os.environ:
             for key in list(os.environ.keys()):
                 if key.startswith("ARXIV_EMAIL__"):
                     del os.environ[key]

        return cls(**settings_kwargs)
