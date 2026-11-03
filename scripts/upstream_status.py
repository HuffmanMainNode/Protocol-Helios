#!/usr/bin/env python3
"""Refresh upstream GitHub repository metadata for the local catalog."""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from scripts.catalog_audit import audit_catalog


def fetch_repository_status(repository: str, token: str | None = None, opener=urlopen) -> dict:
    request = Request(
        f"https://api.github.com/repos/{repository}",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "Protocol-Helios-Catalog-Audit",
            **({"Authorization": f"Bearer {token}"} if token else {}),
        },
        method="GET",
    )
    try:
        with opener(request, timeout=15) as response:
            payload = json.loads(response.read().decode("utf-8"))
            if not isinstance(payload, dict):
                return {"repository": repository, "status": "invalid_response"}
            license_data = payload.get("license") or {}
            return {
                "repository": repository,
                "status": "checked",
                "html_url": payload.get("html_url"),
                "archived": payload.get("archived"),
                "disabled": payload.get("disabled"),
                "default_branch": payload.get("default_branch"),
                "pushed_at": payload.get("pushed_at"),
                "license_spdx_id": license_data.get("spdx_id"),
                "visibility": payload.get("visibility"),
            }
    except HTTPError as error:
        if error.code == 404:
            status = "not_found_or_private"
        elif error.code == 403 and (error.headers or {}).get("X-RateLimit-Remaining") == "0":
            status = "rate_limited"
        elif error.code == 403:
            status = "forbidden"
        else:
            status = f"http_{error.code}"
        return {"repository": repository, "status": status}
    except URLError:
        return {"repository": repository, "status": "network_error"}
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {"repository": repository, "status": "invalid_response"}


def audit_upstreams(
    root: str | Path,
    limit: int | None = None,
    delay: float | None = None,
    token: str | None = None,
    opener=urlopen,
    sleeper=time.sleep,
) -> dict:
    catalog = audit_catalog(root)
    if catalog["errors"]:
        raise ValueError("Catalog validation errors must be fixed before checking upstream status.")
    repositories = catalog["repositories"]
    if limit is None:
        limit = len(repositories) if token else min(50, len(repositories))
    if limit < 1:
        raise ValueError("limit must be at least 1")
    selected = repositories[:limit]
    if delay is None:
        delay = 0.15 if token else 1.1
    if delay < 0:
        raise ValueError("delay cannot be negative")

    results = []
    for index, repository in enumerate(selected):
        result = fetch_repository_status(repository, token=token, opener=opener)
        results.append(result)
        if result["status"] == "rate_limited":
            break
        if index < len(selected) - 1:
            sleeper(delay)

    counts = {}
    for result in results:
        counts[result["status"]] = counts.get(result["status"], 0) + 1

    return {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "source": "GitHub REST API",
        "authenticated": bool(token),
        "catalog_repository_count": len(repositories),
        "requested_limit": limit,
        "attempted_count": len(results),
        "not_attempted_count": len(repositories) - len(results),
        "status_counts": counts,
        "results": results,
        "limitations": [
            "This checks GitHub repository metadata only; it does not inspect source code, dependencies, releases, or security alerts.",
            "A 404 response can mean missing or private; it does not prove why the repository is unavailable.",
            "A recent push does not prove active maintenance or security.",
            "GitHub API metadata does not establish government affiliation or endorsement.",
            "No token checks at most 50 repositories by default to stay within conservative unauthenticated rate limits.",
        ],
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Catalog repository root")
    parser.add_argument("--limit", type=int, help="Maximum repositories to check")
    parser.add_argument("--delay", type=float, help="Seconds between API requests")
    parser.add_argument("--output", help="Optional JSON report path")
    args = parser.parse_args(argv)

    token = os.environ.get("GITHUB_TOKEN")
    try:
        report = audit_upstreams(args.root, args.limit, args.delay, token)
    except (OSError, ValueError) as error:
        print(f"Upstream audit failed: {error}", file=sys.stderr)
        return 2

    rendered = json.dumps(report, indent=2, sort_keys=True)
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 1 if report["status_counts"].get("rate_limited") else 0


if __name__ == "__main__":
    raise SystemExit(main())
