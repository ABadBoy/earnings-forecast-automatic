import unittest
from datetime import datetime

from earnings_forecast.models import Announcement
from earnings_forecast.parsers import parse_announcement
from earnings_forecast.sample_data import SAMPLE_ANNOUNCEMENTS


class ParserTests(unittest.TestCase):
    def test_sample_forecast_types(self) -> None:
        forecasts = [parse_announcement(item) for item in SAMPLE_ANNOUNCEMENTS]

        self.assertEqual(forecasts[0].forecast_type, "预增")
        self.assertEqual(forecasts[1].forecast_type, "扭亏")
        self.assertEqual(forecasts[2].forecast_type, "预减")

    def test_decrease_yoy_is_negative(self) -> None:
        forecast = parse_announcement(SAMPLE_ANNOUNCEMENTS[2])

        self.assertEqual(forecast.yoy_min_percent, -68.0)
        self.assertEqual(forecast.yoy_max_percent, -55.0)

    def test_real_table_format_with_commas_and_en_dash(self) -> None:
        announcement = _announcement(
            "归属于上市公司股东的净利润 盈利：15,500万元–19,500万元 "
            "比上年同期上升：61.62%-103.33%"
        )

        forecast = parse_announcement(announcement)

        self.assertEqual(forecast.net_profit_min_yuan, 155_000_000)
        self.assertEqual(forecast.net_profit_max_yuan, 195_000_000)
        self.assertEqual(forecast.yoy_min_percent, 61.62)
        self.assertEqual(forecast.yoy_max_percent, 103.33)

    def test_real_table_format_with_comma_percentages(self) -> None:
        announcement = _announcement(
            "归属于上市公司股东的净利润 盈利：27,000.00万元-30,000.00万元 "
            "比上年同期增长：4,286.61% - 4,774.01%"
        )

        forecast = parse_announcement(announcement)

        self.assertEqual(forecast.net_profit_min_yuan, 270_000_000)
        self.assertEqual(forecast.net_profit_max_yuan, 300_000_000)
        self.assertEqual(forecast.yoy_min_percent, 4286.61)
        self.assertEqual(forecast.yoy_max_percent, 4774.01)

    def test_single_negative_profit_value(self) -> None:
        announcement = _announcement("预计2026年半年度实现归属于上市公司股东的净利润为-1.79亿元，预计增亏0.48亿元。")

        forecast = parse_announcement(announcement)

        self.assertEqual(forecast.forecast_type, "续亏")
        self.assertEqual(forecast.net_profit_min_yuan, -179_000_000)
        self.assertEqual(forecast.net_profit_max_yuan, -179_000_000)


def _announcement(text: str) -> Announcement:
    return Announcement(
        stock_code="000000",
        stock_name="测试公司",
        title="2026年半年度业绩预告",
        publish_time=datetime(2026, 7, 1),
        source_url="https://example.com/test.pdf",
        text=text,
    )


if __name__ == "__main__":
    unittest.main()
