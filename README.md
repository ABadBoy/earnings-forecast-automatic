# A股每日业绩预告自动化自媒体系统 MVP

这是一个先跑通主链路的 MVP：

1. 导入公告文本样例
2. 识别业绩预告类型与关键财务区间
3. 生成每日结构化数据
4. 生成微信公众号可编辑的 Markdown/HTML 素材

当前版本不依赖第三方包，方便先在本地验证。后续可以逐步接入巨潮资讯、PDF 解析、AI 抽取和微信公众号草稿箱 API。

## 快速开始

可选：安装 PDF 文本解析依赖。

```powershell
python -m pip install -r requirements.txt
```

```powershell
python -m earnings_forecast run-sample
```

生成文件：

```text
data/outputs/YYYY-MM-DD/forecasts.json
data/outputs/YYYY-MM-DD/article.md
data/outputs/YYYY-MM-DD/article.html
```

运行测试：

```powershell
python -m unittest discover -s tests
```

抓取巨潮资讯并生成当天素材：

```powershell
python -m earnings_forecast run-cninfo --date 2026-07-01 --max-pages 3 --limit 20
```

参数说明：

- `--date`：公告日期。
- `--max-pages`：查询巨潮列表页数。
- `--limit`：最多下载并解析多少份 PDF，便于先小批量验证。

真实抓取会生成：

```text
data/downloads/cninfo/YYYY-MM-DD/*.pdf
data/outputs/YYYY-MM-DD/cninfo_announcements.json
data/outputs/YYYY-MM-DD/announcements.json
data/outputs/YYYY-MM-DD/failed_downloads.json
data/outputs/YYYY-MM-DD/forecasts.json
data/outputs/YYYY-MM-DD/article.md
data/outputs/YYYY-MM-DD/article.html
```

其中：

- `cninfo_announcements.json`：巨潮公告列表原始清单。
- `announcements.json`：PDF 已成功下载并解析出的正文。
- `failed_downloads.json`：下载或解析失败的公告，便于后续重试。

## 项目结构

```text
earnings_forecast/
  cli.py              命令行入口
  config.py           配置
  models.py           数据模型
  pipeline.py         MVP 主流程
  parsers.py          业绩预告规则抽取
  renderers.py        文章生成
  sample_data.py      样例公告
data/
  outputs/            输出目录
```

## MVP 边界

已完成：

- 本地样例公告导入
- 巨潮资讯公告列表抓取
- PDF 下载与文本抽取适配
- 业绩预告类型识别
- 净利润区间、同比区间规则抽取
- 原因摘要提取
- 日报 Markdown/HTML 生成

下一步建议：

- 用大模型替换/增强规则抽取
- 为扫描版 PDF 增加 OCR
- 增加人工审核后台
- 接入微信公众号草稿箱 API
