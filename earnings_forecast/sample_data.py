from datetime import datetime

from .models import Announcement


SAMPLE_ANNOUNCEMENTS = [
    Announcement(
        stock_code="000001",
        stock_name="平安银行",
        title="2026年半年度业绩预告",
        publish_time=datetime(2026, 7, 1, 19, 10),
        source_url="https://example.com/000001.pdf",
        text=(
            "公司预计2026年半年度归属于上市公司股东的净利润为120000万元至145000万元，"
            "比上年同期增长35.20%至63.40%。业绩变动主要原因是零售业务收入增长、"
            "资产质量改善及成本费用管控效果显现。"
        ),
    ),
    Announcement(
        stock_code="300001",
        stock_name="特锐德",
        title="2026年半年度业绩预告",
        publish_time=datetime(2026, 7, 1, 20, 5),
        source_url="https://example.com/300001.pdf",
        text=(
            "公司预计2026年半年度归属于上市公司股东的净利润为8500万元至10500万元，"
            "较上年同期扭亏为盈。报告期内，公司充电网业务订单交付增加，"
            "同时期间费用率有所下降。"
        ),
    ),
    Announcement(
        stock_code="600001",
        stock_name="邯郸钢铁",
        title="关于2026年半年度业绩预减的公告",
        publish_time=datetime(2026, 7, 1, 21, 35),
        source_url="https://example.com/600001.pdf",
        text=(
            "经财务部门初步测算，预计2026年半年度实现归属于上市公司股东的净利润"
            "30000万元到42000万元，与上年同期相比减少55%到68%。"
            "本期钢材价格波动、原材料成本上升，对公司盈利能力造成压力。"
        ),
    ),
]

