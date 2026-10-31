"""Which task-building artifacts exist in each of the 48 released tasks (pinned commit)."""
from __future__ import annotations

import json
import os
import re
import urllib.request

from . import sources as S

PROBLEMS = "tasks/frontier-cs-2.0-demo/problems/"
ARTIFACTS = {
    "beat spec (judge/beat_spec.json)": r"/judge/beat_spec\.json$",
    "policy (policy.json)": r"^[^/]+/[^/]+/policy\.json$",
    "file-hash lock (upstream.lock.json)": r"^[^/]+/[^/]+/upstream\.lock\.json$",
    "train/eval workload descriptors (datasets/)": r"/datasets/eval\.json$",
    "reference patch (judge/reference.patch)": r"/judge/reference\.patch$",
    "patch-surface checker (judge/submission_patch.py)": r"/judge/submission_patch\.py$",
    "runtime qualification receipt": r"qualification[^/]*\.json$",
    "statistical calibration record": r"calibration[^/]*\.json$",
}


def tree() -> list[str]:
    cache = S.DATA / "gh" / f"tree-{S.GH_REVISION}.json"
    if not cache.exists():
        url = f"https://api.github.com/repos/{S.GH_REPO}/git/trees/{S.GH_REVISION}?recursive=1"
        headers = {"User-Agent": "fcs2audit/0.1"}
        if os.environ.get("GITHUB_TOKEN"):  # optional: avoids the anonymous API rate limit
            headers["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=120) as r:
            data = json.loads(r.read())
        if data.get("truncated"):
            raise RuntimeError("GitHub tree listing truncated")
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps([t["path"] for t in data["tree"] if t["type"] == "blob"]))
    return json.loads(cache.read_text())


def artifact_coverage(paths: list[str] | None = None) -> dict:
    """For each artifact, the tasks that have it. Paths are relative to the category dir."""
    paths = paths if paths is not None else tree()
    by_task: dict[str, list[str]] = {}
    for p in paths:
        if not p.startswith(PROBLEMS):
            continue
        rest = p[len(PROBLEMS):]  # <Category>/<task>/...
        parts = rest.split("/")
        if len(parts) >= 3:
            by_task.setdefault(parts[1], []).append(rest)
    out = {"tasks": len(by_task), "artifacts": {}}
    for name, pat in ARTIFACTS.items():
        have = sorted(t for t, files in by_task.items()
                      if any(re.search(pat, f) and "/history/" not in f for f in files))
        out["artifacts"][name] = {"count": len(have), "tasks": have if len(have) < len(by_task) else "all"}
    return out
