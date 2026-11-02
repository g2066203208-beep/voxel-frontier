# Channel indexing correction

Independent review found that the OpenFAST binary header contains `nchan+1` names with `names[0] = Time`, while the packed data matrix contains `nchan` non-time columns. Therefore a named channel at header index `i` maps to packed data column `i-1`.

The earlier `FORMAL_36CASE_CHANNEL_METRICS.csv`, `FORMAL_36CASE_CONTROL_RANKING.csv`, `FORMAL_36CASE_GROUP_SUMMARY.csv`, and the earlier control-channel extraction are superseded because they used the unshifted header index. They must not be used for paper results.

Corrected files are:

- `FORMAL_36CASE_CHANNEL_METRICS_CORRECTED.csv`
- `FORMAL_36CASE_CONTROL_RANKING_CORRECTED.csv`
- `FORMAL_36CASE_GROUP_SUMMARY_CORRECTED.csv`

The corrected analysis uses `names.index(channel)-1` and records `mapping=names_index_minus_1`. This correction does not change the OpenFAST run status, actual damping preflight, BTS identity, or binary output integrity.
