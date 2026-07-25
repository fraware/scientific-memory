# ActionCalibrationRecord.v1

Calibration of decision-time predictions against realized outcomes. Never invents probabilities.

## Predictions and missingness

`prediction_presence` is required for `success`, `information_gain`, `cost`, `time`, and `risk`.

- When a flag is `false`, the corresponding `predicted_*` field must be `null`.
- When a flag is `true`, the corresponding value is required.

## Calibration classes

Admissible values: `well_calibrated`, `overconfident`, `underconfident`, `misprioritized`, `inadmissible_action`, `indeterminate`, `not_aggregable`.

## Aggregation eligibility

`aggregation_eligibility` must be `false` when:

- delayed outcome is unresolved
- `realized_outcome_id` is missing
- schema or integrity mismatch would make the record unsafe to pool

`aggregation_eligibility=true` requires `realized_outcome_id`.

## Non-claim

Calibration updates append to the action chain; they do not rewrite claim status. Append with:

```bash
uv run --project pipeline sm add-calibration path/to/ActionCalibrationRecord.v1.json
```
