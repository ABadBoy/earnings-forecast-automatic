import json
from datetime import date
from pathlib import Path

from .cninfo import CninfoParseFailure, download_and_parse_announcements_with_failures, fetch_cninfo_announcements
from .config import settings
from .models import Announcement, CninfoAnnouncement, EarningsForecast
from .parsers import parse_announcement
from .renderers import render_html, render_markdown
from .sample_data import SAMPLE_ANNOUNCEMENTS


def run_sample(report_date: date | None = None) -> Path:
    target_date = report_date or date.today()
    return run_pipeline(SAMPLE_ANNOUNCEMENTS, target_date)


def run_cninfo(report_date: date | None = None, *, max_pages: int = 3, limit: int | None = None) -> Path:
    target_date = report_date or date.today()
    cninfo_items = fetch_cninfo_announcements(target_date, max_pages=max_pages)
    download_dir = settings.download_root / "cninfo" / target_date.isoformat()
    parse_result = download_and_parse_announcements_with_failures(cninfo_items, download_dir, limit=limit)
    output_dir = run_pipeline(parse_result.announcements, target_date)
    _write_cninfo_items(output_dir / "cninfo_announcements.json", cninfo_items)
    _write_failures(output_dir / "failed_downloads.json", parse_result.failures)
    return output_dir


def run_pipeline(announcements: list[Announcement], report_date: date) -> Path:
    forecasts = [parse_announcement(item) for item in announcements]
    output_dir = settings.output_root / report_date.isoformat()
    output_dir.mkdir(parents=True, exist_ok=True)

    _write_raw_announcements(output_dir / "announcements.json", announcements)
    _write_json(output_dir / "forecasts.json", forecasts)
    (output_dir / "article.md").write_text(render_markdown(forecasts, report_date), encoding="utf-8")
    (output_dir / "article.html").write_text(render_html(forecasts, report_date), encoding="utf-8")
    return output_dir


def _write_json(path: Path, forecasts: list[EarningsForecast]) -> None:
    payload = [item.to_dict() for item in forecasts]
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_raw_announcements(path: Path, announcements: list[Announcement]) -> None:
    payload = [
        {
            "stock_code": item.stock_code,
            "stock_name": item.stock_name,
            "title": item.title,
            "publish_time": item.publish_time.isoformat(timespec="minutes"),
            "source_url": item.source_url,
            "text": item.text,
        }
        for item in announcements
    ]
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_cninfo_items(path: Path, items: list[CninfoAnnouncement]) -> None:
    payload = [
        {
            "stock_code": item.stock_code,
            "stock_name": item.stock_name,
            "title": item.title,
            "publish_timestamp_ms": item.publish_timestamp_ms,
            "source_url": item.pdf_url,
            "announcement_id": item.announcement_id,
        }
        for item in items
    ]
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_failures(path: Path, failures: list[CninfoParseFailure]) -> None:
    payload = [item.to_dict() for item in failures]
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
