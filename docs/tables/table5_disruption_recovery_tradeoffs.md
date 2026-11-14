# Table 5: Disruption Recovery Robustness Under Unexpected Worker Absences

| Absent Workers | Recovery Strategy | Solver Status | Schedule Churn (Shifts Disrupted) | Repaired Headcount | Runtime (s) | Feasibility Verified |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Recovery MILP (Stability-Preserving) | OPTIMAL | 2 | 25 | 0.0178 | True |
| 1 | Full Reschedule from Scratch | INFEASIBLE | 27 | 0 | 0.0095 | True |
| 2 | Recovery MILP (Stability-Preserving) | OPTIMAL | 5 | 22 | 0.0182 | True |
| 2 | Full Reschedule from Scratch | INFEASIBLE | 27 | 0 | 0.0090 | True |
| 3 | Recovery MILP (Stability-Preserving) | OPTIMAL | 8 | 19 | 0.0169 | True |
| 3 | Full Reschedule from Scratch | INFEASIBLE | 27 | 0 | 0.0076 | True |
