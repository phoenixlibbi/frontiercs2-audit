# Findings (generated)

Computed by `python -m fcs2audit.report` from `FrontierCS2/FrontierCS-2-runs@10a1e897` and `FrontierCS/FrontierCS-2@0de64ff8`. 912 runs, 19 models, 48 tasks, 870 final patches (each checked against its published sha256).

## 1. The release reproduces the paper

| Agent | Passes | Pass rate | Paper |
|---|---|---|---|
| opus | 28/48 | 58% | 58% |
| astra | 21/48 | 44% | 44% |
| gemini | 19/48 | 40% | 40% |
| sol | 17/48 | 35% | 35% |
| glm | 12/48 | 25% | 25% |
| k3 | 10/48 | 21% | 21% |
| wonder | 10/48 | 21% | 21% |
| ds | 7/48 | 15% | 15% |
| muse | 6/48 | 12% | 12% |
| qwen | 6/48 | 12% | 12% |
| glmf | 6/48 | 12% | 12% |
| step | 4/48 | 8% | 8% |

Tasks no reported agent passes: **16** (paper: 16). All match: **True**.

Mean margins (Figure 6) differ from the release by a near-constant offset (+2.23 to +2.33) for every agent, so the gaps between agents reproduce; the absolute level depends on reference values not in the release (no reference score recorded for: vllm_llm_serving_optimization).

## 2. Verdicts agree with the per-metric checks

In all 858 graded runs, PASS holds exactly when every hidden check is met (0 mismatches).

## 3. A higher score is not a pass (paper's 12 agents)

242 of the 379 runs whose final score is above the reference's still FAIL. 5 runs PASS with a score at or below the reference: ckks_composable_noise/gemini, ckks_composable_noise/k3, ckks_composable_noise/qwen, ckks_composable_noise/sol, ckks_composable_noise/wonder.

## 4. One check decides many failures (paper's 12 agents)

57 of 401 graded failures missed exactly one hidden (metric, workload) check. Missed metrics: makespan_seconds 6, compression_ratio 4, branch_accuracy 4, batch_latency_seconds 3, lpips 3, attack_success_rate 3, selected_runtime_seconds 2, worst_finish_time_fairness_rho 2, elapsed_seconds 2, lloyd_loop_latency_ms 2, lookup_ns 2, search_overhead_seconds 2, gap 2, delta 2, tflops 2, inception_fdr 1, cpu_time_seconds 1, inference_latency_ms 1, throughput_ops_per_second 1, refuted_pair 1, residual_update_seconds 1, latency_ms 1, runtime_seconds 1, historical_query_us 1, training_latency_ms 1, ema_quantized_png_psnr_db 1, search_latency_ms 1, ocr_reward 1, branches_covered 1, case_throughput_ktps 1, paired_timing 1.

Sensitivity only (not a proposed rule): passes if one missed check were allowed.

| Agent | Passes | + one-miss fails |
|---|---|---|
| astra | 21 | 28 |
| ds | 7 | 17 |
| gemini | 19 | 21 |
| glm | 12 | 19 |
| glmf | 6 | 9 |
| k3 | 10 | 14 |
| muse | 6 | 6 |
| opus | 28 | 32 |
| qwen | 6 | 10 |
| sol | 17 | 24 |
| step | 4 | 9 |
| wonder | 10 | 14 |

## 5. Progent: both passing patches detect the attack by its known text

Task rule (Progent README): "Policies have to follow from the user's request, not from a list of known attacker strings."

Passing runs: carbon-g, gemini-agy. Passing patches matching 3+ AgentDojo `important_instructions` phrases: carbon-g, gemini-agy.

| Model | Verdict | AgentDojo phrases in added lines |
|---|---|---|
| astra | FAIL | none |
| carbon-g | PASS | <INFORMATION> (2), This is an important message from (1), Before you can solve the task that I gave you (1), Signed, (1) |
| ds | FAIL | After you do that (1) |
| ds1017 | FAIL | <INFORMATION> (1) |
| fable51 | FAIL | <INFORMATION> (2) |
| gemini | FAIL | <INFORMATION> (11), please do the following first (1), After you do that (1) |
| gemini-agy | PASS | <INFORMATION> (11), This is an important message from (1), please do the following first (1), After you do that (1), Signed, (1) |
| glm | FAIL | <INFORMATION> (6), This is an important message from (3), please do the following first (4), Signed, (1) |
| glmf | FAIL | <INFORMATION> (2) |
| k27 | FAIL | <INFORMATION> (7) |
| k3 | FAIL | <INFORMATION> (3), This is an important message from (1), Before you can solve the task that I gave you (1) |
| k31 | FAIL | <INFORMATION> (2) |
| muse | FAIL | <INFORMATION> (2), After you do that (1), Signed, (1) |
| opus | FAIL | <INFORMATION> (1), This is an important message from (1), please do the following first (1), After you do that (1) |
| qwen | FAIL | <INFORMATION> (6), This is an important message from (1), After you do that (1) |
| sol | FAIL | none |
| step | FAIL | none |
| terra | FAIL | <INFORMATION> (2) |
| wonder | FAIL | <INFORMATION> (3) |

A phrase mention alone is not proof of a detector; the two passing patches were read by hand (see docs/VERIFICATION.md).

## 6. Reruns (not a finding)

`other_runs` holds 656 non-accepted runs (346 graded). On 277 clean comparisons the verdict pairs (accepted/other) are FAIL/FAIL 154, FAIL/PASS 50, PASS/FAIL 30, PASS/PASS 43. Cause of each rerun is not in the release and internal task-version ids are omitted, so disagreement here is NOT an estimate of run-to-run noise.
