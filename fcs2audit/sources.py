"""Pinned sources: every number in this repo is computed from these exact revisions.

FrontierCS 2 released its formal runs on Hugging Face and its tasks on GitHub.
We pin both so anyone can re-download the same bytes and get the same results.
"""
from __future__ import annotations

import hashlib
import json
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HF_DATASET = "FrontierCS2/FrontierCS-2-runs"
HF_REVISION = "10a1e8971692e35464c06c83d820b2704476f7c1"  # lastModified 2026-10-31T01:06:31Z
GH_REPO = "FrontierCS/FrontierCS-2"
GH_REVISION = "0de64ff83ab07f546824bd2c46860e718c915a8c"  # main on 2026-10-31T19:38:15Z
PAPER = "arXiv:2610.29932v1"

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def hf_url(path: str) -> str:
    return f"https://huggingface.co/datasets/{HF_DATASET}/resolve/{HF_REVISION}/{path}"


def gh_url(path: str) -> str:
    return f"https://raw.githubusercontent.com/{GH_REPO}/{GH_REVISION}/{path}"


def sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "fcs2audit/0.1"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def fetch(url: str, dest: Path, expect_sha: str | None = None) -> Path:
    """Download once; verify the published hash when one is given."""
    if not dest.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        data = _get(url)
        if expect_sha and sha256(data) != expect_sha:
            raise ValueError(f"hash mismatch for {url}")
        dest.write_bytes(data)
    elif expect_sha and sha256(dest.read_bytes()) != expect_sha:
        raise ValueError(f"cached file {dest} does not match {expect_sha}")
    return dest


def results_path() -> Path:
    return fetch(hf_url("metadata/formal-results.json"), DATA / "hf" / "formal-results.json")


def load_results() -> dict:
    return json.loads(results_path().read_text())


def fetch_patches(workers: int = 16) -> int:
    """Download every released final patch and check it against `patch_sha256`."""
    runs = [r for r in load_results()["runs"] if r.get("patch_path")]

    def one(r):
        fetch(hf_url(r["patch_path"]), DATA / "hf" / r["patch_path"], r.get("patch_sha256"))

    with ThreadPoolExecutor(workers) as ex:
        list(ex.map(one, runs))
    return len(runs)


def patch_text(run: dict) -> str | None:
    if not run.get("patch_path"):
        return None
    p = DATA / "hf" / run["patch_path"]
    return p.read_text(errors="replace") if p.exists() else None
