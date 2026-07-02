import json
from datetime import date
from typing import List

import markdown
from openai import OpenAI

from .config import settings
from .models import Announcement

SYSTEM_PROMPT = """你是一个专业的 A 股资深财经编辑。
你的任务是根据提供的今日上市公司业绩预告【原始文本】，撰写一篇适合微信公众号发布的业绩预告日报。

请严格按照以下格式和要求输出 Markdown 格式的纯文本：

**核心要求**：
1. **只关注业绩增长的公司**：你需要仔细阅读提供的所有公司公告文本，筛选出**净利润实现同比增长**（预增、扭亏等）的公司。对于亏损、预减、不确定的公司，请直接忽略。
2. **格式必须与样例完全一致**：不需要大标题，第一段直接是总体概览，接着是各个公司的详细情况。
3. **不要输出任何表格**。
4. **提取准确的数据和原因**：由于输入的是原始公告文本，你需要自己准确地找出该公司的净利润区间、同比增长区间，并精炼其业绩变动的主要原因。
5. **大额数字转换**：如果文章里的金额达到或超过 1 亿（即 10000 万元），请务必将其转换为“亿元”单位，保留一到两位小数，**绝对不要在亿以上的金额使用“万元”**。

**格式样例参考**：

今日，韶能股份（000601）、益生股份（002458）、永太科技（002326）等公司相继披露2026年半年度业绩预告，净利润均实现同比大幅增长，涉及清洁能源、畜禽养殖、锂电材料等多个行业赛道。

## 韶能股份：清洁能源业务“开源节流”驱动增长

韶能股份预计2026年上半年归属于上市公司股东的净利润为1.55亿元至1.95亿元，同比增长61.62%至103.33%；扣非净利润为1.31亿元至1.71亿元，同比增长143.31%至217.71%。

公司表示，业绩增长主要系清洁可再生能源业务通过开展“开源节流”各项工作，促使经营成果同比大幅增长。目前公司主营清洁可再生能源业务包括水电、生物质能发电、光伏等。公司正持续推进源网荷储一体化业务，拟通过拓展绿电、储能、售电业务，以绿电支撑算力发展，促进韶关算电集群高质量发展。同时，精密（智能）制造业务通过拓展市场、内部降本增效等工作，经营成果同比增长；纸制品业务经营业绩同比减亏。

## 益生股份：白羽肉鸡景气度上行

（在这里写益生股份的具体利润数据和增长原因，格式同上）
"""

def render_article_with_llm(announcements: List[Announcement], report_date: date) -> tuple[str, str]:
    if not settings.llm_api_key:
        raise ValueError("LLM_API_KEY is not set.")

    client = OpenAI(
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
    )

    # 1. 准备给大模型的数据（直接传原始文本）
    data_payload = [
        {
            "stock_code": a.stock_code,
            "stock_name": a.stock_name,
            "title": a.title,
            "text": a.text,
        }
        for a in announcements
    ]
    
    # 2. 调用大模型
    user_prompt = f"以下是 {report_date.isoformat()} 披露的业绩预告原始文本，请阅读并筛选出业绩增长的公司，按照样例格式生成推文：\n{json.dumps(data_payload, ensure_ascii=False, indent=2)}"
    
    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.7,
    )
    
    llm_content = response.choices[0].message.content.strip()

    # 3. 组装最终的 Markdown (直接加上标题和声明)
    title = f"{settings.brand_name}：{report_date.isoformat()} 业绩增长公司概览"
    
    final_markdown = f"# {title}\n\n{llm_content}\n\n## 数据说明\n\n本文内容由 AI 根据上市公司正式公告原始文本辅助生成。内容仅用于信息整理，不构成投资建议。"
    
    # 4. 渲染为 HTML
    html_body = markdown.markdown(final_markdown)
    
    # 微信公众号草稿箱不支持 <style> 标签，必须使用内联样式 (Inline CSS)
    h1_style = "font-size: 24px; line-height: 1.4; font-weight: bold; margin-bottom: 24px; color: #111827;"
    h2_style = "margin-top: 32px; margin-bottom: 16px; font-size: 20px; color: #1d4ed8; font-weight: bold; padding-left: 12px; border-left: 5px solid #1d4ed8;"
    p_style = "margin: 20px 0; text-align: justify; font-size: 16px; color: #374151; letter-spacing: 0.5px; line-height: 2.0;"
    
    html_body = html_body.replace('<h1>', f'<h1 style="{h1_style}">')
    html_body = html_body.replace('<h2>', f'<h2 style="{h2_style}">')
    html_body = html_body.replace('<p>', f'<p style="{p_style}">')
    
    final_html = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>{title}</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; color: #1f2937; max-width: 760px; margin: 0 auto; padding: 24px;">
  {html_body}
</body>
</html>"""
    
    return final_markdown, final_html
