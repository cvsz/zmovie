from __future__ import annotations

import argparse
import json
import re
from typing import Any

from .repository import delete_project, list_projects

_PROJECT_ID = re.compile(r"^prj_[A-Za-z0-9]+$")


def project_ids(prefix: str = "prj_") -> list[str]:
    ids: list[str] = []
    for item in list_projects(limit=500):
        project_id = str(item.get("id") or "")
        if project_id.startswith(prefix) and _PROJECT_ID.fullmatch(project_id):
            ids.append(project_id)
    return sorted(set(ids))


def delete_projects(prefix: str = "prj_") -> dict[str, Any]:
    ids = project_ids(prefix)
    deleted: list[str] = []
    for project_id in ids:
        if delete_project(project_id):
            deleted.append(project_id)
    remaining = project_ids(prefix)
    return {
        "prefix": prefix,
        "requested": ids,
        "deleted": deleted,
        "remaining": remaining,
        "complete": not remaining,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="List or delete zMovie project rows by the safe prj_ prefix")
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list", help="List safe project IDs")
    p_list.add_argument("--prefix", default="prj_")

    p_delete = sub.add_parser("delete", help="Delete projects from SQLite; filesystem cleanup is handled by the operator wrapper")
    p_delete.add_argument("--prefix", default="prj_")
    p_delete.add_argument("--confirm", required=True)

    args = parser.parse_args(argv)
    if args.prefix != "prj_":
        print("project reset error: only the exact prj_ prefix is accepted")
        return 2

    if args.command == "list":
        ids = project_ids(args.prefix)
        print(json.dumps({"prefix": args.prefix, "count": len(ids), "project_ids": ids}, indent=2))
        return 0

    if args.confirm != "DELETE-ALL-PRJ":
        print("project reset error: confirmation must be DELETE-ALL-PRJ")
        return 2

    result = delete_projects(args.prefix)
    print(json.dumps(result, indent=2))
    return 0 if result["complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
