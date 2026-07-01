from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    project_root: Path = Path(__file__).resolve().parent.parent
    output_root: Path = project_root / "data" / "outputs"
    download_root: Path = project_root / "data" / "downloads"
    brand_name: str = "A股业绩预告日报"


settings = Settings()
