from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class CninfoAnnouncement:
    stock_code: str
    stock_name: str
    title: str
    publish_timestamp_ms: int
    adjunct_url: str
    announcement_id: str

    @property
    def pdf_url(self) -> str:
        if self.adjunct_url.startswith("http"):
            return self.adjunct_url
        return f"https://static.cninfo.com.cn/{self.adjunct_url.lstrip('/')}"


@dataclass(frozen=True)
class Announcement:
    stock_code: str
    stock_name: str
    title: str
    publish_time: datetime
    source_url: str
    text: str


@dataclass(frozen=True)
class EarningsForecast:
    stock_code: str
    stock_name: str
    title: str
    publish_time: str
    source_url: str
    forecast_type: str
    report_period: str
    net_profit_min_yuan: float | None
    net_profit_max_yuan: float | None
    yoy_min_percent: float | None
    yoy_max_percent: float | None
    reason_summary: str
    confidence_score: float
    risk_flags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
