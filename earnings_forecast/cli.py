import argparse
from datetime import date

from .pipeline import run_cninfo, run_sample


def main() -> None:
    parser = argparse.ArgumentParser(description="A-share earnings forecast content MVP")
    parser.add_argument("--use-llm", action="store_true", help="Use LLM to generate content")
    parser.add_argument("--publish", action="store_true", help="Publish to WeChat")
    subparsers = parser.add_subparsers(dest="command", required=True)

    sample_parser = subparsers.add_parser("run-sample", help="Run the pipeline with bundled sample announcements")
    sample_parser.add_argument("--date", help="Report date, format YYYY-MM-DD")

    cninfo_parser = subparsers.add_parser("run-cninfo", help="Fetch CNINFO announcements and generate content")
    cninfo_parser.add_argument("--date", help="Report date, format YYYY-MM-DD")
    cninfo_parser.add_argument("--max-pages", type=int, default=3, help="CNINFO result pages to query")
    cninfo_parser.add_argument("--limit", type=int, help="Maximum PDFs to download and parse")

    args = parser.parse_args()
    if args.command == "run-sample":
        report_date = date.fromisoformat(args.date) if args.date else None
        output_dir = run_sample(report_date, use_llm=args.use_llm, publish=args.publish)
        print(f"Generated MVP outputs: {output_dir}")
    elif args.command == "run-cninfo":
        report_date = date.fromisoformat(args.date) if args.date else None
        output_dir = run_cninfo(report_date, max_pages=args.max_pages, limit=args.limit, use_llm=args.use_llm, publish=args.publish)
        print(f"Generated CNINFO outputs: {output_dir}")
