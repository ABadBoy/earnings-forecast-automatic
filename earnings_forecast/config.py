import os
from dataclasses import dataclass, field
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

@dataclass(frozen=True)
class Settings:
    project_root: Path = Path(__file__).resolve().parent.parent
    output_root: Path = project_root / "data" / "outputs"
    download_root: Path = project_root / "data" / "downloads"
    brand_name: str = "A股业绩预告日报"
    
    # LLM Settings (Defaults to DeepSeek)
    llm_api_key: str = field(default_factory=lambda: os.getenv("LLM_API_KEY", ""))
    llm_base_url: str = field(default_factory=lambda: os.getenv("LLM_BASE_URL", "https://api.deepseek.com"))
    llm_model: str = field(default_factory=lambda: os.getenv("LLM_MODEL", "deepseek-chat"))
    
    # WeChat Settings
    wechat_app_id: str = field(default_factory=lambda: os.getenv("WECHAT_APP_ID", ""))
    wechat_app_secret: str = field(default_factory=lambda: os.getenv("WECHAT_APP_SECRET", ""))
    wechat_thumb_media_id: str = field(default_factory=lambda: os.getenv("WECHAT_THUMB_MEDIA_ID", ""))

settings = Settings()
