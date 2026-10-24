Validation
----------

## <Model or feature>

The question this validation answers, and how to run it:

	python validate_<name>.py          # build and cache inputs
	marimo run validate_<name>_marimo.py

### Inputs

| Input | File | Basis |
| ----- | ---- | ----- |
| ... | ... | source, units, conventions (e.g. UTC hour beginning) |

### Procedure

1. Step-by-step description, naming the functions that implement each step.

### Results

Date/version of the run, then a metrics table (e.g. energy error, peak
error, MAPE, CV(RMSE), bias, R², correlation) for each variant compared.

### Known gaps

- Differences in definition between model and reference, data limitations.

## Comparison to existing methods

| Method | Spatial unit | Test design | Metric |
| ------ | ------------ | ----------- | ------ |

## References

1. ...
