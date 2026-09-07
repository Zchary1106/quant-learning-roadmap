"""Opt-in, read-only schema check for a real Tushare Pro daily response.

Run without arguments to confirm the safety gate. To actually make one
authenticated request, explicitly pass --live and --allow-insecure-http after
reviewing the provider's current transport and terms. This script cannot trade.
"""

from __future__ import annotations

import argparse
import os
import sys

from quantdesk.health import check_tushare_daily_schema
from quantdesk.providers import TushareProProvider, UrllibJsonTransport
from quantdesk.providers.tushare import TUSHARE_PRO_URL


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Read-only QuantDesk Tushare schema check")
    parser.add_argument("--live", action="store_true", help="permit one authenticated read")
    parser.add_argument(
        "--allow-insecure-http",
        action="store_true",
        help="required for the provider's documented HTTP endpoint",
    )
    parser.add_argument("--base-url", default=TUSHARE_PRO_URL)
    parser.add_argument("--ts-code", default="600000.SH")
    parser.add_argument("--start-date", default="20260901")
    parser.add_argument("--end-date", default="20260904")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.live:
        print("No request sent. Add --live only for an explicit read-only health check.")
        return 0
    if not args.allow_insecure_http and args.base_url.startswith("http://"):
        print(
            "Refusing request: the configured endpoint is HTTP. Review transport security "
            "and rerun with --allow-insecure-http only if you accept it.",
            file=sys.stderr,
        )
        return 2
    if not os.getenv("TUSHARE_TOKEN"):
        print("TUSHARE_TOKEN is not configured; no request sent.", file=sys.stderr)
        return 2

    provider = TushareProProvider.from_environment(
        transport=UrllibJsonTransport(allow_insecure_http=args.allow_insecure_http),
        base_url=args.base_url,
    )
    result = check_tushare_daily_schema(
        provider,
        ts_code=args.ts_code,
        start_date=args.start_date,
        end_date=args.end_date,
    )
    print(
        f"endpoint={result.endpoint} rows={result.row_count} "
        f"schema_matches_design={result.schema_matches_design}"
    )
    print(f"observed_fields={','.join(result.observed_fields)}")
    if result.missing_required_fields:
        print(f"missing_required_fields={','.join(result.missing_required_fields)}")
        return 1
    print("This only checks one returned schema. It does not verify data completeness or PIT.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
