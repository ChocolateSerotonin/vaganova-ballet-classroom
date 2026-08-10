# Vaganova Classroom Simulator — Final Calibrated Code

This folder contains the final calibrated model files.

## Files
- `agents.py` — student and teacher agent behavior.
- `model.py` — classroom model, parameters, independent random streams, scheduling, and data collection.
- `run.py` — one illustrative 18-class run (`seed=42`).
- `calibrate.py` — final multi-seed validation (`500 × 18` classes).

## Final parameter set
- `new_student_lambda = 1.30`
- `first_return_prob = 0.30`
- `delayed_return_prob = 0.12`
- `delayed_return_window = 2`
- `second_return_prob = 0.50`
- `stable_attend_prob = 0.70`
- `alpha = 10`
- `gamma = 15`
- `beta = 1`
- `performance_sigma = 0.15`
- `eta_B = 1`
- `B_max = 100`
- `eta_E_low = 0.02`
- `eta_E_high = 0.04`
- `internalization_acceleration_after = 6`
- `level_target_base = 16`
- `level_target_growth = 1.25`
- `mastery_threshold_ratio = 0.60`
- `newcomer_difficulty_threshold = 0.50`
- `forgetting_base = 2`
- `forgetting_cap = 8`
- `mastery_retention_floor = 0.50`

## Run
```powershell
python run.py
python calibrate.py
```

`run.py` is an illustrative seeded trajectory. `calibrate.py` is the validation script and should be used for distributional evidence.

## Modeling conventions retained
- All 8 students in Class 1 are first-time students.
- Empty classes are operationally coded as `New_Ratio = 1.0`, preventing curriculum advancement while preserving existing upgrade readiness.
- `L` is the long-term curriculum level; `D` is the actual teaching level for the current class.
- If newcomers are more than half of attendees, `D = max(1, L - 1)`.
- Teacher evaluation still refers to long-term level `L` even when `D < L`.
- Latent mastery and observed performance are distinct.
- Absence-related forgetting applies after any prior attendance (`C > 0`).
- Arrival, initial attributes, attendance/retention, and performance use independent random streams.
