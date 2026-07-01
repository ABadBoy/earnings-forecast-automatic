import json
import time
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .models import Announcement, CninfoAnnouncement
from .pdf_text import extract_pdf_text


CNINFO_QUERY_URL = "https://www.cninfo.com.cn/new/hisAnnouncement/query"
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
    ),
    "Referer": "https://www.cninfo.com.cn/new/commonUrl/pageOfSearch?url=disclosure/list/search",
    "X-Requested-With": "XMLHttpRequest",
    "Accept": "application/json, text/javascript, */*; q=0.01",
}


class CninfoError(RuntimeError):
    pass


@dataclass(frozen=True)
class CninfoParseFailure:
    stock_code: str
    stock_name: str
    title: str
    source_url: str
    error: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class CninfoParseResult:
    announcements: list[Announcement]
    failures: list[CninfoParseFailure]


def fetch_cninfo_announcements(
    target_date: date,
    *,
    search_key: str = "业绩预告",
    page_size: int = 30,
    max_pages: int = 3,
) -> list[CninfoAnnouncement]:
    announcements: list[CninfoAnnouncement] = []
    for page_num in range(1, max_pages + 1):
        payload = _query_page(target_date, search_key, page_num, page_size)
        page_items = parse_cninfo_payload(payload)
        announcements.extend(page_items)
        total = int(payload.get("totalAnnouncement", 0) or 0)
        if len(announcements) >= total or not page_items:
            break
        time.sleep(0.4)
    return _deduplicate(announcements)


def parse_cninfo_payload(payload: dict[str, Any]) -> list[CninfoAnnouncement]:
    items = payload.get("announcements") or []
    parsed = []
    for item in items:
        adjunct_url = str(item.get("adjunctUrl") or "")
        title = _clean_title(str(item.get("announcementTitle") or ""))
        stock_code = str(item.get("secCode") or item.get("证券代码") or "")
        stock_name = str(item.get("secName") or item.get("证券简称") or "")
        timestamp = int(item.get("announcementTime") or 0)
        announcement_id = str(item.get("announcementId") or adjunct_url or f"{stock_code}-{timestamp}")
        if not adjunct_url or not stock_code or not title:
            continue
        parsed.append(
            CninfoAnnouncement(
                stock_code=stock_code,
                stock_name=stock_name,
                title=title,
                publish_timestamp_ms=timestamp,
                adjunct_url=adjunct_url,
                announcement_id=announcement_id,
            )
        )
    return parsed


def download_and_parse_announcements(
    items: list[CninfoAnnouncement],
    download_dir: Path,
    *,
    limit: int | None = None,
) -> list[Announcement]:
    return download_and_parse_announcements_with_failures(items, download_dir, limit=limit).announcements


def download_and_parse_announcements_with_failures(
    items: list[CninfoAnnouncement],
    download_dir: Path,
    *,
    limit: int | None = None,
) -> CninfoParseResult:
    download_dir.mkdir(parents=True, exist_ok=True)
    selected = items[:limit] if limit is not None else items
    announcements = []
    failures = []
    for item in selected:
        try:
            pdf_path = download_pdf(item, download_dir)
            text = extract_pdf_text(pdf_path)
            announcements.append(
                Announcement(
                    stock_code=item.stock_code,
                    stock_name=item.stock_name,
                    title=item.title,
                    publish_time=_from_cninfo_timestamp(item.publish_timestamp_ms),
                    source_url=item.pdf_url,
                    text=text,
                )
            )
        except Exception as exc:  # noqa: BLE001 - batch jobs should record and continue.
            failures.append(
                CninfoParseFailure(
                    stock_code=item.stock_code,
                    stock_name=item.stock_name,
                    title=item.title,
                    source_url=item.pdf_url,
                    error=str(exc),
                )
            )
    return CninfoParseResult(announcements=announcements, failures=failures)


def download_pdf(item: CninfoAnnouncement, download_dir: Path) -> Path:
    safe_name = _safe_filename(f"{item.stock_code}_{item.announcement_id}.pdf")
    path = download_dir / safe_name
    if path.exists() and path.stat().st_size > 0:
        return path

    request = Request(item.pdf_url, headers={**DEFAULT_HEADERS, "Accept": "application/pdf,*/*"})
    try:
        with urlopen(request, timeout=30) as response:
            content = response.read()
    except (HTTPError, URLError, TimeoutError) as exc:
        raise CninfoError(f"Failed to download PDF {item.pdf_url}: {exc}") from exc

    if not content.startswith(b"%PDF"):
        raise CninfoError(f"Downloaded file is not a PDF: {item.pdf_url}")
    path.write_bytes(content)
    return path


def _query_page(target_date: date, search_key: str, page_num: int, page_size: int) -> dict[str, Any]:
    encoded = urlencode(
        {
            "pageNum": page_num,
            "pageSize": page_size,
            "column": "szse",
            "tabName": "fulltext",
            "plate": "",
            "stock": "",
            "searchkey": search_key,
            "secid": "",
            "category": "category_yjyg_szsh",
            "trade": "",
            "seDate": f"{target_date.isoformat()}~{target_date.isoformat()}",
            "sortName": "",
            "sortType": "",
            "isHLtitle": "true",
        }
    ).encode("utf-8")
    request = Request(CNINFO_QUERY_URL, data=encoded, headers=DEFAULT_HEADERS, method="POST")
    try:
        with urlopen(request, timeout=30) as response:
            body = response.read().decode("utf-8")
    except (HTTPError, URLError, TimeoutError) as exc:
        raise CninfoError(f"Failed to query CNINFO announcements: {exc}") from exc

    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise CninfoError("CNINFO returned a non-JSON response") from exc


def _from_cninfo_timestamp(value: int) -> datetime:
    if value <= 0:
        return datetime.now()
    return datetime.fromtimestamp(value / 1000)


def _clean_title(value: str) -> str:
    return value.replace("<em>", "").replace("</em>", "").strip()


def _safe_filename(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in value)


def _deduplicate(items: list[CninfoAnnouncement]) -> list[CninfoAnnouncement]:
    seen = set()
    unique = []
    for item in items:
        key = item.announcement_id or item.adjunct_url
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique
