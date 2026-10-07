# 06 · IBM Quantum hardware runbook (+10 bonus)

## 0. Account (one-time, ~5 min)
1. Sign in at **https://quantum.cloud.ibm.com** (IBM Quantum Platform). The free **Open Plan** gives a monthly allowance of QPU time. This project needs well under a minute.
2. Copy your **API key** from the dashboard. If you have several instances, also copy the instance **CRN**.
3. Save it **locally, never in the repo**:
   ```bash
   python - <<'PY'
   from qiskit_ibm_runtime import QiskitRuntimeService
   QiskitRuntimeService.save_account(
       channel="ibm_quantum_platform",
       token=input("IBM API key: "),        # typed, not pasted into a file
       # instance="crn:v1:...",            # optional
       set_as_default=True, overwrite=True)
   PY
   ```
   This writes `~/.qiskit/qiskit-ibm.json`, which is outside the repo.
4. Check: `python -c "from qiskit_ibm_runtime import QiskitRuntimeService as S; print([b.name for b in S().backends()])"`

> 🔒 **Token safety.** Never paste the token into Claude Code chat, a notebook cell, `.env` that gets committed, or CI. `pre-commit` runs `detect-secrets`. If a token ever leaks, regenerate it in the dashboard immediately.

## 1. What runs on hardware
- Instance: `hardware_problem` in the config (4 assets, k = 2 → 4 qubits).
- Circuits in **one job** (fewer queue waits):
  - PUB 0: XY-QAOA p=1 with simulator-trained parameters, 8192 shots
  - PUB 1: XY-QAOA p=2 (optional, deeper; shows the depth vs noise trade-off)
  - PUB 2–3: readout calibration (all-0, all-X) on the **same physical qubits** (`initial_layout` = union of the final layouts of PUB 0–1, since routing may move them)
- Options: XY4 dynamical decoupling, gate + measurement twirling.
- Expected QPU usage: a few seconds.

## 2. Commands
Parameters are trained on the statevector simulator (`qaoa.optimize`, config `qaoa` restarts/maxiter);
hardware only runs the fixed angles. Every mode prints the cost gap between the best and second-best basket.
```bash
# Rehearsal: identical PUBs through the identical SamplerV2 code path, on FakeTorino (local, no account)
python scripts/run_hardware.py --dry-run           # → results/hardware/dry_run_fake_torino.json

# Day 1, ~23:30: submit and go to sleep
python scripts/run_hardware.py --submit            # least-busy backend, or --backend ibm_torino
# → writes results/hardware/pending.json  {job_id, backend, submitted_at, circuits, layout, params}

# Day 2 morning
python scripts/run_hardware.py --status
python scripts/run_hardware.py --collect           # → results/hardware/<job_id>.json + metrics
python scripts/make_figures.py                     # noise_ladder.png gets the hardware bar
```

## 3. Evidence to commit (judges can verify it)
`results/hardware/<job_id>.json` contains: job ID, backend name, timestamps, physical qubit layout, transpiled depth and 2q count, raw counts for every PUB, the calibration matrices, the metrics (raw / post-selected / mitigated), and the backend properties snapshot (median T1/T2, readout error and 2q error on the used qubits).
Also commit a screenshot of the job page from the IBM dashboard: `results/hardware/job_screenshot.png`.

## 4. If things go wrong
| Problem | Action |
|---|---|
| Queue > 6 h | Keep the job, and also run on a different backend with a shorter queue (`service.backends()` → pending_jobs) |
| `IBMNotAuthorizedError` | Re-save the account; check the instance CRN |
| Results are pure noise | Report it honestly; show that p=1 survives better than p=2 and that post-selection helps. That is still a valid noise-aware result |
| `--status` shows `ERROR` (it prints `job.error_message()`) | Save `results/hardware/failed_<job_id>.json` with the message, fix, dry-run, resubmit. Error 3211 "Options field seed_simulator is not valid" = simulator options sent to a real device (pitfall #11, fixed) |
| Job not done by 12:30 Day 2 | Submit with the job ID + "pending" in README; the noisy-sim ladder carries the story |
