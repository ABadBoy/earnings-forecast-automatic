import unittest
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from earnings_forecast.cninfo import download_and_parse_announcements_with_failures, parse_cninfo_payload
from earnings_forecast.models import CninfoAnnouncement


class CninfoTests(unittest.TestCase):
    def test_parse_payload_removes_highlight_tags(self) -> None:
        payload = {
            "announcements": [
                {
                    "secCode": "000001",
                    "secName": "平安银行",
                    "announcementTitle": "2026年半年度<em>业绩预告</em>",
                    "announcementTime": 1782927600000,
                    "announcementId": "1219999999",
                    "adjunctUrl": "finalpage/2026-07-01/1219999999.PDF",
                }
            ]
        }

        items = parse_cninfo_payload(payload)

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].stock_code, "000001")
        self.assertEqual(items[0].title, "2026年半年度业绩预告")
        self.assertEqual(items[0].pdf_url, "https://static.cninfo.com.cn/finalpage/2026-07-01/1219999999.PDF")

    def test_parse_payload_skips_incomplete_items(self) -> None:
        payload = {
            "announcements": [
                {"secCode": "000001", "announcementTitle": "缺少 PDF"},
                {"adjunctUrl": "finalpage/x.pdf", "announcementTitle": "缺少代码"},
            ]
        }

        self.assertEqual(parse_cninfo_payload(payload), [])

    def test_download_parse_batch_records_failures(self) -> None:
        items = [
            CninfoAnnouncement("000001", "平安银行", "业绩预告", 1782927600000, "ok.pdf", "ok"),
            CninfoAnnouncement("000002", "万科A", "业绩预告", 1782927600000, "bad.pdf", "bad"),
        ]

        def fake_download(item: CninfoAnnouncement, download_dir: Path) -> Path:
            if item.stock_code == "000002":
                raise RuntimeError("download failed")
            return download_dir / "ok.pdf"

        with TemporaryDirectory() as temp_dir:
            with patch("earnings_forecast.cninfo.download_pdf", side_effect=fake_download):
                with patch("earnings_forecast.cninfo.extract_pdf_text", return_value="净利润为1万元至2万元，增长10%至20%。"):
                    result = download_and_parse_announcements_with_failures(items, Path(temp_dir))

        self.assertEqual(len(result.announcements), 1)
        self.assertEqual(len(result.failures), 1)
        self.assertEqual(result.announcements[0].publish_time, datetime.fromtimestamp(1782927600000 / 1000))
        self.assertEqual(result.failures[0].stock_code, "000002")


if __name__ == "__main__":
    unittest.main()
