"""Unit tests on small synthetic records, plus pinned-release tests (marked `network`)."""
import pytest

from fcs2audit import analysis as A
from fcs2audit import report
from fcs2audit import sources as S


def run(rid, verdict, checks=None, score=None, ref=None, model="m", task="t"):
    return {"record_id": rid, "verdict": verdict, "checks": checks, "score": score,
            "reference_score": ref, "model_id": model, "task": task}


def test_misses_counts_unmet_metric_workload_checks():
    r = run("a", "FAIL", [{"label": "x", "passed": 143, "total": 144},
                          {"label": "y", "passed": 4, "total": 4}])
    assert A.misses(r) == 1
    assert A.misses(run("b", "FAIL")) == 0


def test_consistency_flags_pass_with_unmet_check():
    res = {"runs": [run("ok", "PASS", [{"label": "x", "passed": 2, "total": 2}]),
                    run("bad", "PASS", [{"label": "x", "passed": 1, "total": 2}])]}
    assert A.consistency(res)["mismatches"] == ["bad"]


def test_pass_vs_score_and_near_misses():
    one = [{"label": "lat", "passed": 5, "total": 6}]
    res = {"runs": [run("a", "FAIL", one, 60, 50), run("b", "PASS", [{"label": "lat", "passed": 6, "total": 6}], 40, 50),
                    run("c", "FAIL", [{"label": "lat", "passed": 3, "total": 6}], 70, 50)]}
    pvs = A.pass_vs_score(res)
    assert (pvs["runs_above_reference"], pvs["above_but_fail"]) == (2, 2)
    assert pvs["pass_at_or_below_reference"] == ["b"]
    nm = A.near_misses(res)
    assert (nm["graded_fails"], nm["one_miss"], nm["missed_metric"]) == (2, 1, {"lat": 1})


def test_attack_text_markers_match_plain_text_and_regex_source():
    plain = "+ s = 'This is an important message from me'\n+ '<INFORMATION>'\n"
    regex = '+ re.compile(r"please\\s+do\\s+the\\s+following\\s+first")\n+ r"Signed,\\s*"\n'
    assert set(A.attack_text_markers(plain)) == {"This is an important message from", "<INFORMATION>"}
    assert set(A.attack_text_markers(regex)) == {"please do the following first", "Signed,"}
    assert A.attack_text_markers("- removed 'Signed,'\n context <INFORMATION>\n") == {}


# ---- pinned release: these numbers are the ones quoted in the README ----

@pytest.fixture(scope="module")
def findings():
    return report.build()


@pytest.mark.network
def test_release_reproduces_paper_headline(findings):
    rp = findings["reproduce"]
    assert rp["all_match"] and len(rp["never_passed"]) == 16
    assert rp["agents"]["opus"]["passes"] == 28


@pytest.mark.network
def test_release_counts_and_consistency(findings):
    assert findings["counts"] == {"runs": 912, "models": 19, "tasks": 48, "patches": 870}
    assert findings["consistency"]["graded_runs"] == 858
    assert findings["consistency"]["mismatches"] == []


@pytest.mark.network
def test_pinned_findings(findings):
    ps, nm = findings["pass_vs_score_paper12"], findings["near_misses_paper12"]
    assert (ps["above_but_fail"], ps["runs_above_reference"]) == (242, 379)
    assert (nm["one_miss"], nm["graded_fails"]) == (57, 401)
    pg = findings["progent_attack_text"]
    assert pg["passing"] == ["carbon-g", "gemini-agy"] == pg["passing_with_markers"]


@pytest.mark.network
def test_task_artifact_coverage(findings):
    a = findings["task_artifacts"]
    assert a["tasks"] == 48
    counts = {k.split(" (")[0]: v["count"] for k, v in a["artifacts"].items()}
    assert counts["beat spec"] == counts["policy"] == counts["file-hash lock"] == 48
    assert counts["reference patch"] == 45


def test_artifact_coverage_on_synthetic_tree():
    p = "tasks/frontier-cs-2.0-demo/problems/Theory/"
    tree = [p + "a/judge/beat_spec.json", p + "a/policy.json", p + "b/policy.json",
            p + "a/judge/reference/history/old/runtime-qualification.json"]
    from fcs2audit import tasks as T
    c = T.artifact_coverage(tree)
    assert c["tasks"] == 2
    assert c["artifacts"]["policy (policy.json)"]["count"] == 2
    assert c["artifacts"]["beat spec (judge/beat_spec.json)"]["tasks"] == ["a"]
    assert c["artifacts"]["runtime qualification receipt"]["count"] == 0  # history/ ignored


def test_sources_are_pinned_to_commits():
    assert len(S.HF_REVISION) == 40 and len(S.GH_REVISION) == 40
    assert S.HF_REVISION in S.hf_url("x") and S.GH_REVISION in S.gh_url("x")
