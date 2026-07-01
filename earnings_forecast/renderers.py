from collections import Counter
from datetime import date
from html import escape

from .config import settings
from .models import EarningsForecast


def render_markdown(forecasts: list[EarningsForecast], report_date: date) -> str:
    title = _build_title(forecasts, report_date)
    lines = [
        f"# {title}",
        "",
        _build_digest(forecasts),
        "",
        "## 今日概览",
        "",
        _render_overview(forecasts),
        "",
        "## 重点公司",
        "",
        "| 代码 | 公司 | 类型 | 净利润区间 | 同比区间 | 主要原因 |",
        "| --- | --- | --- | --- | --- | --- |",
    ]

    for item in forecasts:
        lines.append(
            "| {code} | {name} | {kind} | {profit} | {yoy} | {reason} |".format(
                code=item.stock_code,
                name=item.stock_name,
                kind=item.forecast_type,
                profit=_format_profit_range(item),
                yoy=_format_yoy_range(item),
                reason=item.reason_summary,
            )
        )

    risk_lines = _render_risks(forecasts)
    if risk_lines:
        lines.extend(["", "## 风险提示", "", *risk_lines])

    lines.extend(
        [
            "",
            "## 数据说明",
            "",
            "本文由自动化 MVP 根据公告文本生成，财务数据以公司正式公告为准。内容仅用于信息整理，不构成投资建议。",
        ]
    )
    return "\n".join(lines) + "\n"


def render_html(forecasts: list[EarningsForecast], report_date: date) -> str:
    markdown = render_markdown(forecasts, report_date)
    rows = "\n".join(_render_html_row(item) for item in forecasts)
    risks = "".join(
        f"<li>{escape(item.stock_name)}：{escape('；'.join(item.risk_flags))}</li>"
        for item in forecasts
        if item.risk_flags
    )
    risk_section = f"<h2>风险提示</h2><ul>{risks}</ul>" if risks else ""

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(_build_title(forecasts, report_date))}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; line-height: 1.75; color: #1f2937; max-width: 760px; margin: 0 auto; padding: 24px; }}
    h1 {{ font-size: 26px; line-height: 1.35; }}
    h2 {{ margin-top: 28px; font-size: 20px; }}
    .digest {{ padding: 12px 14px; background: #f3f4f6; border-left: 4px solid #2563eb; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
    th, td {{ border-bottom: 1px solid #e5e7eb; padding: 8px 6px; text-align: left; vertical-align: top; }}
    th {{ background: #f9fafb; }}
    .note {{ color: #6b7280; font-size: 13px; }}
  </style>
</head>
<body>
  <h1>{escape(_build_title(forecasts, report_date))}</h1>
  <p class="digest">{escape(_build_digest(forecasts))}</p>
  <h2>今日概览</h2>
  <p>{escape(_render_overview(forecasts))}</p>
  <h2>重点公司</h2>
  <table>
    <thead><tr><th>代码</th><th>公司</th><th>类型</th><th>净利润区间</th><th>同比区间</th><th>主要原因</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
  {risk_section}
  <h2>数据说明</h2>
  <p class="note">本文由自动化 MVP 根据公告文本生成，财务数据以公司正式公告为准。内容仅用于信息整理，不构成投资建议。</p>
  <!-- Markdown source:
{escape(markdown)}
  -->
</body>
</html>
"""


def _build_title(forecasts: list[EarningsForecast], report_date: date) -> str:
    return f"{settings.brand_name}：{report_date.isoformat()} 共{len(forecasts)}家公司披露"


def _build_digest(forecasts: list[EarningsForecast]) -> str:
    counts = Counter(item.forecast_type for item in forecasts)
    parts = [f"{kind}{count}家" for kind, count in counts.most_common()]
    return "今日业绩预告样本显示：" + "，".join(parts) + "。"


def _render_overview(forecasts: list[EarningsForecast]) -> str:
    counts = Counter(item.forecast_type for item in forecasts)
    return "；".join(f"{kind}：{count}家" for kind, count in counts.most_common())


def _render_risks(forecasts: list[EarningsForecast]) -> list[str]:
    lines = []
    for item in forecasts:
        if item.risk_flags:
            lines.append(f"- {item.stock_name}：{'；'.join(item.risk_flags)}")
    return lines


def _render_html_row(item: EarningsForecast) -> str:
    cells = [
        item.stock_code,
        item.stock_name,
        item.forecast_type,
        _format_profit_range(item),
        _format_yoy_range(item),
        item.reason_summary,
    ]
    return "<tr>" + "".join(f"<td>{escape(cell)}</td>" for cell in cells) + "</tr>"


def _format_profit_range(item: EarningsForecast) -> str:
    if item.net_profit_min_yuan is None or item.net_profit_max_yuan is None:
        return "未识别"
    return f"{item.net_profit_min_yuan / 100_000_000:.2f}亿至{item.net_profit_max_yuan / 100_000_000:.2f}亿元"


def _format_yoy_range(item: EarningsForecast) -> str:
    if item.yoy_min_percent is None or item.yoy_max_percent is None:
        return "未识别"
    return f"{item.yoy_min_percent:.2f}%至{item.yoy_max_percent:.2f}%"

