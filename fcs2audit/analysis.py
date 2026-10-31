"""Checks on the released FrontierCS 2 runs. Each function returns plain data.

Nothing here runs a model or a task: every number comes from the pinned
`formal-results.json` and the released final patches (see `sources.py`).
"""
from __future__ import annotations

import re
import statistics
from collections import Counter, defaultdict

# The 12 agents reported in the paper (Figure 2), by their dataset model_id.
PAPER_AGENTS = {
    "opus": 58, "astra": 44, "gemini": 40, "sol": 35, "glm": 25, "k3": 21,
    "wonder": 21, "ds": 15, "muse": 12, "qwen": 12, "glmf": 12, "step": 8,
}
PAPER_NEVER_PASSED = 16  # "No agent passes any of 16 tasks" (Section 1)
ANCHOR = "k27"  # Kimi K2.7: in the fit, not reported (Section 5.2)


def misses(run: dict) -> int:
    """Hidden (metric, workload) checks the final submission did not meet."""
    return sum(c["total"] - c["passed"] for c in run.get("checks") or [])


def reproduce(results: dict) -> dict:
    """Paper headline numbers recomputed from the release."""
    runs = results["runs"]
    by = defaultdict(list)
    for r in runs:
        by[r["model_id"]].append(r)
    agents = {}
    for m, paper_pct in PAPER_AGENTS.items():
        passes = sum(r["verdict"] == "PASS" for r in by[m])
        agents[m] = {"passes": passes, "runs": len(by[m]),
                     "pass_pct": round(100 * passes / len(by[m])), "paper_pct": paper_pct}
    never = sorted(t["task"] for t in results["tasks"]
                   if not any(r["verdict"] == "PASS" for r in runs
                              if r["task"] == t["task"] and r["model_id"] in PAPER_AGENTS))
    return {"agents": agents, "never_passed": never,
            "all_match": all(a["pass_pct"] == a["paper_pct"] for a in agents.values())
            and len(never) == PAPER_NEVER_PASSED}


def margin_offsets(results: dict, paper_fig6: dict[str, float]) -> dict:
    """Mean of (final score - task reference) per agent, every run counted, vs Figure 6.

    The task reference is the median reference score over the 13 fitted agents'
    runs (Appendix D, Step 4). One task (vllm_llm_serving_optimization) records
    no reference score in the release, so the paper's preset value is unknown;
    we use 0 and report the offset to Figure 6 per agent.
    """
    pool = set(PAPER_AGENTS) | {ANCHOR}
    refs = defaultdict(list)
    for r in results["runs"]:
        if r["model_id"] in pool and r.get("reference_score") is not None:
            refs[r["task"]].append(r["reference_score"])
    ref = {t: statistics.median(v) for t, v in refs.items()}
    out = {}
    for m, fig in paper_fig6.items():
        rs = [r for r in results["runs"] if r["model_id"] == m]
        mean = statistics.mean((r["score"] or 0) - ref.get(r["task"], 0.0) for r in rs)
        out[m] = {"mean_margin": round(mean, 2), "figure6": fig, "offset": round(mean - fig, 2)}
    offs = [v["offset"] for v in out.values()]
    return {"agents": out, "offset_min": min(offs), "offset_max": max(offs),
            "tasks_without_reference": sorted(t["task"] for t in results["tasks"] if t["task"] not in ref)}


def consistency(results: dict) -> dict:
    """PASS must mean every hidden check was met, and FAIL that at least one was not."""
    graded = [r for r in results["runs"] if r.get("checks")]
    bad = [r["record_id"] for r in graded
           if (r["verdict"] == "PASS") != (misses(r) == 0)]
    return {"graded_runs": len(graded), "mismatches": bad,
            "pass_without_checks": sum(1 for r in results["runs"]
                                       if r["verdict"] == "PASS" and not r.get("checks"))}


def pass_vs_score(results: dict, models=None) -> dict:
    """How often a final score above the reference still fails, and the reverse."""
    rs = [r for r in results["runs"] if models is None or r["model_id"] in models]
    scored = [r for r in rs if r.get("reference_score") is not None and r["score"] is not None]
    above = [r for r in scored if r["score"] > r["reference_score"]]
    return {"runs_above_reference": len(above),
            "above_but_fail": sum(r["verdict"] == "FAIL" for r in above),
            "pass_at_or_below_reference": sorted(r["record_id"] for r in scored
                                                 if r["verdict"] == "PASS" and r["score"] <= r["reference_score"])}


def near_misses(results: dict, models=None) -> dict:
    """Failed graded runs that missed exactly one hidden (metric, workload) check."""
    rs = [r for r in results["runs"] if models is None or r["model_id"] in models]
    failed = [r for r in rs if r["verdict"] == "FAIL" and r.get("checks")]
    one = [r for r in failed if misses(r) == 1]
    metric = Counter(next(c["label"] for c in r["checks"] if c["passed"] < c["total"]) for r in one)
    per_agent = {}
    for m in sorted({r["model_id"] for r in rs}):
        mine = [r for r in rs if r["model_id"] == m]
        per_agent[m] = {"passes": sum(r["verdict"] == "PASS" for r in mine),
                        "one_miss_fails": sum(1 for r in one if r["model_id"] == m)}
    return {"graded_fails": len(failed), "one_miss": len(one),
            "one_miss_records": sorted(r["record_id"] for r in one),
            "missed_metric": dict(metric.most_common()), "per_agent": per_agent}


def reruns(results: dict) -> dict:
    """Non-accepted runs kept in `other_runs`. The release gives no reason for them."""
    acc = {r["record_id"]: r for r in results["runs"]}
    clean = [x for x in results["other_runs"]
             if x["relation"] == "same_formal_evaluation" and x["platform_state"] == "COMPLETED"
             and x.get("verdict") and acc[x["record_id"]]["verdict"]
             and acc[x["record_id"]]["result_source"] == "original run's own final verification"]
    pairs = Counter((acc[x["record_id"]]["verdict"], x["verdict"]) for x in clean)
    return {"other_runs": len(results["other_runs"]),
            "graded_other_runs": sum(1 for x in results["other_runs"] if x.get("verdict")),
            "clean_comparisons": len(clean),
            "verdict_pairs": {f"{a}/{b}": n for (a, b), n in sorted(pairs.items())},
            "note": "Cause of each rerun is not in the release and internal task-version ids "
                    "are omitted, so disagreement here is NOT an estimate of run-to-run noise."}


# AgentDojo's `important_instructions` attack text (ethz-spylab/agentdojo@089ed468,
# src/agentdojo/attacks/important_instructions_attacks.py, `_JB_STRING`).
AGENTDOJO_PHRASES = [
    "<INFORMATION>",
    "This is an important message from",
    "Before you can solve the task that I gave you",
    "please do the following first",
    "After you do that",
    "Signed,",
]
# Between words, a patch may write a plain space or regex source such as `\s+`, `\s*`.
_GAP = r"(?:\s+|\\s[+*]?|\[\^?\\s\][+*]?)+"


def _phrase_regex(phrase: str) -> str:
    if phrase == "<INFORMATION>":
        return r"<\s*(?:\\s\*\s*)?INFORMATION"
    return _GAP.join(re.escape(w) for w in phrase.split())


AGENTDOJO_MARKERS = {p: _phrase_regex(p) for p in AGENTDOJO_PHRASES}
PROGENT_RULE = ("Policies have to follow from the user's request, not from a list of known "
                "attacker strings.")  # Progent task README, repo/README.md line 64


def added_lines(patch: str) -> list[str]:
    return [l[1:] for l in patch.splitlines() if l.startswith("+") and not l.startswith("+++")]


def attack_text_markers(patch: str) -> dict[str, int]:
    """Count AgentDojo attack-template markers written into the patch's added lines."""
    text = "\n".join(added_lines(patch))
    return {k: len(re.findall(p, text, re.IGNORECASE)) for k, p in AGENTDOJO_MARKERS.items()
            if re.search(p, text, re.IGNORECASE)}


def progent_attack_text(results: dict, patch_text) -> dict:
    """Which Progent final patches match on AgentDojo's known attack text."""
    rows = []
    for r in sorted((x for x in results["runs"] if x["task"] == "progent_privilege_control"),
                    key=lambda x: x["model_id"]):
        p = patch_text(r) or ""
        rows.append({"model": r["model_id"], "verdict": r["verdict"],
                     "markers": attack_text_markers(p)})
    passing = [x for x in rows if x["verdict"] == "PASS"]
    return {"rule": PROGENT_RULE, "runs": rows,
            "passing": [x["model"] for x in passing],
            "passing_with_markers": [x["model"] for x in passing if len(x["markers"]) >= 3]}
