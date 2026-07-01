import re

from .models import Announcement, EarningsForecast


FORECAST_KEYWORDS = {
    "扭亏": ["扭亏", "扭亏为盈"],
    "预减": ["预减", "减少", "下降"],
    "首亏": ["首亏"],
    "续亏": ["续亏"],
    "预增": ["预增", "增长", "增加", "上升"],
}

NUMBER_PATTERN = r"-?\d[\d,]*(?:\.\d+)?"
AMOUNT_UNIT_PATTERN = r"万元|亿元|元"
RANGE_SEPARATOR_PATTERN = r"(?:至|到|-|－|–|—|~)"


def parse_announcement(announcement: Announcement) -> EarningsForecast:
    text = _normalize_text(announcement.text)
    title = _normalize_text(announcement.title)
    combined = f"{title} {text}"

    forecast_type = _detect_forecast_type(title, text)
    report_period = _detect_report_period(combined)
    net_profit_min, net_profit_max = _extract_net_profit_range(text)
    forecast_type = _adjust_forecast_type_by_profit(forecast_type, text, net_profit_min, net_profit_max)
    yoy_min, yoy_max = _extract_yoy_range(text)
    reason_summary = _extract_reason_summary(text)
    confidence = _score_confidence(forecast_type, net_profit_min, net_profit_max, yoy_min, yoy_max)

    return EarningsForecast(
        stock_code=announcement.stock_code,
        stock_name=announcement.stock_name,
        title=announcement.title,
        publish_time=announcement.publish_time.isoformat(timespec="minutes"),
        source_url=announcement.source_url,
        forecast_type=forecast_type,
        report_period=report_period,
        net_profit_min_yuan=net_profit_min,
        net_profit_max_yuan=net_profit_max,
        yoy_min_percent=yoy_min,
        yoy_max_percent=yoy_max,
        reason_summary=reason_summary,
        confidence_score=confidence,
        risk_flags=_detect_risk_flags(text),
    )


def _normalize_text(value: str) -> str:
    value = value.replace("\u3000", " ")
    return re.sub(r"\s+", "", value)


def _detect_forecast_type(title: str, text: str) -> str:
    for forecast_type, keywords in FORECAST_KEYWORDS.items():
        if any(keyword in title for keyword in keywords):
            return forecast_type

    # In body text, negative earnings signals should win over generic words such as
    # "上升", which often describe costs instead of profit.
    for forecast_type, keywords in FORECAST_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return forecast_type
    return "不确定"


def _adjust_forecast_type_by_profit(
    forecast_type: str,
    text: str,
    net_profit_min: float | None,
    net_profit_max: float | None,
) -> str:
    if net_profit_min is None or net_profit_max is None:
        return forecast_type
    if net_profit_max < 0:
        if "增亏" in text or "续亏" in text:
            return "续亏"
        if "首亏" in text:
            return "首亏"
        return "预亏"
    if net_profit_min > 0 and "扭亏" in text and "上年同期" in text:
        return "扭亏"
    return forecast_type


def _detect_report_period(text: str) -> str:
    patterns = [
        r"20\d{2}年半年度",
        r"20\d{2}年年度",
        r"20\d{2}年第一季度",
        r"20\d{2}年第三季度",
        r"20\d{2}年前三季度",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    return "未识别"


def _extract_net_profit_range(text: str) -> tuple[float | None, float | None]:
    range_match = _search_amount_range(text)
    if range_match:
        lower = _amount_to_yuan(range_match.group("min"), range_match.group("min_unit"))
        upper = _amount_to_yuan(range_match.group("max"), range_match.group("max_unit"))
        return (min(lower, upper), max(lower, upper))

    single_match = _search_single_net_profit(text)
    if single_match:
        value = _amount_to_yuan(single_match.group("value"), single_match.group("unit"))
        return value, value

    return None, None


def _extract_yoy_range(text: str) -> tuple[float | None, float | None]:
    pattern = (
        rf"(?P<direction>增长|增加|上升|减少|下降)"
        rf"[:：]?"
        rf"(?P<min>{NUMBER_PATTERN})%"
        rf"{RANGE_SEPARATOR_PATTERN}"
        rf"(?P<max>{NUMBER_PATTERN})%"
    )
    match = re.search(pattern, text)
    if not match:
        return None, None

    lower = _number_to_float(match.group("min"))
    upper = _number_to_float(match.group("max"))
    if match.group("direction") in {"减少", "下降"}:
        lower = -abs(lower)
        upper = -abs(upper)
    return (min(lower, upper), max(lower, upper))


def _search_amount_range(text: str) -> re.Match[str] | None:
    amount_range = (
        rf"(?P<min>{NUMBER_PATTERN})(?P<min_unit>{AMOUNT_UNIT_PATTERN})"
        rf"{RANGE_SEPARATOR_PATTERN}"
        rf"(?P<max>{NUMBER_PATTERN})(?P<max_unit>{AMOUNT_UNIT_PATTERN})"
    )
    preferred_contexts = [
        rf"归属于上市公司股东的净利润.*?(?:盈利|亏损)?[:：]?{amount_range}",
        rf"净利润(?:为|约为|预计为|实现|预计实现)?(?:正值且)?(?:盈利|亏损)?[:：]?{amount_range}",
        rf"(?:预计|实现).*?净利润.*?(?:盈利|亏损)?[:：]?{amount_range}",
    ]
    for pattern in preferred_contexts:
        match = re.search(pattern, text)
        if match:
            return match

    return re.search(amount_range, text)


def _search_single_net_profit(text: str) -> re.Match[str] | None:
    pattern = (
        rf"归属于上市公司股东的净利润"
        rf".{{0,40}}?"
        rf"(?:为|约为|预计为|实现)?"
        rf"(?P<value>{NUMBER_PATTERN})(?P<unit>{AMOUNT_UNIT_PATTERN})"
    )
    return re.search(pattern, text)


def _amount_to_yuan(value: str, unit: str) -> float:
    unit_multiplier = {"元": 1, "万元": 10_000, "亿元": 100_000_000}[unit]
    return _number_to_float(value) * unit_multiplier


def _number_to_float(value: str) -> float:
    return float(value.replace(",", ""))


def _extract_reason_summary(text: str) -> str:
    markers = ["主要原因是", "业绩变动主要原因是", "报告期内，", "本期"]
    for marker in markers:
        if marker in text:
            summary = text.split(marker, 1)[1]
            summary = re.split(r"[。；;]", summary, maxsplit=1)[0]
            return summary.strip("，,。 ")[:120]
    return "公告未提取到明确原因摘要"


def _detect_risk_flags(text: str) -> list[str]:
    flags = []
    if "非经常性损益" in text:
        flags.append("关注非经常性损益影响")
    if "成本上升" in text or "价格波动" in text:
        flags.append("关注成本或价格波动")
    if "不确定" in text:
        flags.append("公告存在不确定性表述")
    return flags


def _score_confidence(
    forecast_type: str,
    net_profit_min: float | None,
    net_profit_max: float | None,
    yoy_min: float | None,
    yoy_max: float | None,
) -> float:
    score = 0.35
    if forecast_type != "不确定":
        score += 0.25
    if net_profit_min is not None and net_profit_max is not None:
        score += 0.25
    if yoy_min is not None and yoy_max is not None:
        score += 0.15
    return round(min(score, 1.0), 2)
