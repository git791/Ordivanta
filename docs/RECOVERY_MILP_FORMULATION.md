# Recovery MILP Mathematical Formulation

## 1. Overview
Ordivanta provides two distinct mathematical optimisation paradigms:
1. **Original Baseline Two-Stage MILP:** Treats shift coverage as an immutable hard constraint ($\sum_i x_{ijs} \ge d_{js}$). If demand exceeds feasible supply, it truthfully reports `INFEASIBLE`.
2. **Lexicographic Recovery MILP:** Specifically designed for operational disruption scenarios (high absenteeism, demand surges, specialist shortages). It models uncovered demand explicitly using non-negative shortage variables $s_{js} \ge 0$ and optimizes via a three-stage lexicographic hierarchy.

---

## 2. Sets and Indices
- $I$: Set of employees, indexed by $i$.
- $J$: Set of production units/cells, indexed by $j$.
- $S$: Set of shifts in planning horizon, indexed by $s$.
- $C$: Set of shift conflict pairs $(s_1, s_2)$ violating temporal overlap or minimum rest $R_{\min}$.
- $K$: Set of skills.

---

## 3. Parameters
- $d_{js}$: Required staffing headcount for unit $j$ on shift $s$.
- $w_{js}^{\text{crit}}$: Criticality weight (5.0 for critical safety units, 1.0 otherwise).
- $h_s$: Duration of shift $s$ in hours.
- $a_{is} \in \{0, 1\}$: Binary availability parameter.
- $q_{ij} \in \{0, 1\}$: Qualification indicator under chosen `QualificationPolicy` (`ANY`, `ALL`, or `LEVEL_AND_CERTIFICATION`).
- $H_i^{\text{reg}}$: Regular scheduled working hours limit.
- $H_i^{\text{ot}}$: Maximum allowed voluntary overtime hours ($0$ if employee opted out).
- $c_i^{\text{base}}$: Base hourly pay rate.
- $c_i^{\text{ot}}$: Additive overtime hourly premium (typically $0.5 \times c_i^{\text{base}}$).
- $x_{ijs}^0 \in \{0, 1\}$: Pre-existing / locked schedule assignment.

---

## 4. Decision Variables
- $x_{ijs} \in \{0, 1\}$: Assignment of employee $i$ to unit $j$ on shift $s$.
- $s_{js} \ge 0$: Uncovered staffing shortage for unit $j$ on shift $s$.
- $o_i \ge 0$: Overtime hours scheduled for employee $i$ ($0 \le o_i \le H_i^{\text{ot}}$).
- $u_i \ge 0$: Absolute workload fairness deviation from target workload $\bar{H}_i$.

---

## 5. Hard Constraints (Enforced in All Stages)

### 5.1 Coverage with Shortages
$$\sum_{i \in I} x_{ijs} + s_{js} \ge d_{js} \quad \forall j \in J, s \in S$$

### 5.2 Single Assignment per Shift
$$\sum_{j \in J} x_{ijs} \le 1 \quad \forall i \in I, s \in S$$

### 5.3 Pairwise Temporal Conflicts & Minimum Rest
For all conflicting shift pairs $(s_1, s_2) \in C$:
$$\sum_{j \in J} x_{ij s_1} + \sum_{j \in J} x_{ij s_2} \le 1 \quad \forall i \in I$$

### 5.4 Regular Hours & Overtime Limit
$$L_i = \sum_{j \in J} \sum_{s \in S} h_s x_{ijs} \quad \forall i \in I$$
$$L_i \le H_i^{\text{reg}} + o_i \quad \forall i \in I$$
$$o_i \ge L_i - H_i^{\text{reg}} \quad \forall i \in I$$
$$0 \le o_i \le H_i^{\text{ot}} \quad \forall i \in I$$

### 5.5 Eligibility & Qualification
$$x_{ijs} = 0 \quad \text{if } a_{is} = 0 \lor q_{ij} = 0 \lor \text{employee is absent}$$

### 5.6 Locked Assignments
$$x_{ijs} = 1 \quad \forall (i, j, s) \text{ locked in original schedule}$$

---

## 6. Lexicographic Recovery Stages

### Stage 1: Maximize Coverage (Minimize Uncovered Shortages)
$$Z_1^* = \min \sum_{j \in J} \sum_{s \in S} w_{js}^{\text{crit}} s_{js}$$
Subject to all hard constraints (5.1–5.6).

### Stage 2: Minimize Labor Cost & Overtime Premium
$$\min Z_2 = \sum_{i \in I} \left( c_i^{\text{base}} L_i + c_i^{\text{ot}} o_i \right)$$
Subject to:
$$\sum_{j \in J} \sum_{s \in S} w_{js}^{\text{crit}} s_{js} \le Z_1^*$$
and all hard constraints.

### Stage 3: Workload Fairness & Preference Penalties
$$\min Z_3 = \sum_{i \in I} u_i + 0.001 Z_2$$
Subject to:
$$u_i \ge L_i - \bar{H}_i \quad \forall i \in I$$
$$u_i \ge \bar{H}_i - L_i \quad \forall i \in I$$
$$Z_2 \le Z_2^* (1 + \epsilon)$$
$$\sum_{j \in J} \sum_{s \in S} w_{js}^{\text{crit}} s_{js} \le Z_1^*$$
and all hard constraints.

---

## 7. Status & Optimality Reporting
- `OPTIMAL` is returned if and only if HiGHS/CBC proves global mathematical optimality in all solved stages.
- If any stage halts at time-limit with an incumbent, `FEASIBLE` is reported.
- If hard constraints cannot be satisfied even with shortages, `INFEASIBLE` is reported.
