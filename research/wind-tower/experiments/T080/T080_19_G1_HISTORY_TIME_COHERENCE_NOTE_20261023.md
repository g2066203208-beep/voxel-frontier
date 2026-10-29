# T080.19 G1 history timestamp audit (2026-10-23)

SOURCE: T070/extract_t070_g1.py blob 8dc8a8c4e82b3f07b94244eb3616be7262f0b910, directly read in full. Function history_last stores h.data[-1][1] without its step-time h.data[-1][0]. Thus extracted SOF/SOM values do not preserve proof of simultaneous sampling across six components, three sections, and the Gravity field frame. This is a static evidence gap, NOT a claim of an actual ODB mismatch.

OFFICIAL: Abaqus 2025, Writing history output data (HistoryOutput.data pairs): https://docs.software.vt.edu/abaqusv2025/English/SIMACAECMDRefMap/simacmd-c-odbintrowritehistpyc.htm

RUN-T08019-SYNTH-001: standalone read-only timestamp checker and 11 synthetic unit tests, 11/11 PASS. Code SHA-256 f5b68ab0adf05da4af011a286b13c2973e0e04af10a68cc7963d94c14cbfc259. This note does not upload the checker and does not claim a native Abaqus run. Numeric timestamp tolerance 1e-8 s is not a physical acceptance threshold.

HOLD: T057/T070 native G0/G1, HRB335/HRB500 branch, P0 vs Pe, 30 joints, signed 6D balance, seismic W/E/WE, material fatigue, optimization and licensed standard-clause acceptance.

NEXT: read true T070 Gravity ODB time-tagged SOF1-3/SOM1-3 for IOS_C31_TOP, IOS_S01_BOTTOM, IOS_TOWER_BASE and native logs before any physical acceptance. No physical mother-model change.