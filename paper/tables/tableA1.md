Table: Table A1. Integer check of near-zero lower bounds

| Cell | LP z lower | Integer z lower (solver bound) | Integer z incumbent | Prop. 4 y lower (integer, solver bound) | y at integer allocation | Solves at time limit |
|-----------------------------------------|----------|----------|----------|----------|-----------|----------|
| 2012 within-district, η = 0, δ = 1 | 0.0077 | 0.0077 | 0.0077 | 0.0069 | 0.0070 | 0/50 |
| 2026 within-district, η = 0.1, δ = 0.1 | 0.0137 | 0.0139 | 0.0139 | 0.0098 | 0.0106 | 10/50 |
| 2026 within-district, calibrated, δ = 0.1 | 0.0104 | 0.0106 | 0.0106 | 0.0065 | 0.0072 | 7/50 |
| 2025 within-district, η = 0, δ = 0.1 | 0.0017 | 0.0018 | 0.0018 | −0.0020 | −0.0006 | 2/50 |
| 2024 within-constituency, η = 0, δ = 0.1 | 0.0036 | 0.0037 | 0.0037 | 0.0078 | 0.0092 | 1/96 |
| 2022 within-district, η = 0, δ = 0.1 | 0.0144 | 0.0145 | 0.0145 | 0.0187 | 0.0204 | 3/50 |

*Notes.* Mixed-integer programs use the same constraint matrices as the LPs, including the 2026 zones. Each solve has a 30-second limit, extended to 180 seconds when no integer solution has been found. Solver bound: the best bound proven by the solver when it stops, which is a valid lower bound on the integer minimum also when the time limit is reached; the incumbent is the best integer allocation found. These optimization checks exclude the residents' early-composition restriction, for which optimization did not finish within an hour. Integer witnesses for the main specification are reported separately in Table A2.
