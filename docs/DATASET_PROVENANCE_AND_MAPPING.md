# Dataset Provenance, Audit, and Constraint Compatibility Report

## 1. Final Dataset Governance Policy

In accordance with project direction, external benchmark sprawl is strictly constrained to prioritize our existing benchmarks:
1. **Primary Manufacturing Benchmark:** Ordivanta Synthetic Manufacturing Benchmark (kept and extended with realistic disruption, skills proficiency, absenteeism, and overtime layers).
2. **Shift Scheduling Benchmark:** Kept existing `instances1_225` dataset (225 raw TXT instances).
3. **Personnel Task Scheduling (PTSP):** Kept existing `ptask/ptsp` dataset (137 raw DAT instances) as a supplementary specialist/task-allocation benchmark.
4. **Nurse Rostering Benchmark:** Kept confirmed existing `instances1_24` dataset (24 raw TXT + 24 ROS instances) with transparent mapping.
5. **Deferred Repositories:** Remote KAHO and INRC-II integrations are deferred as the existing 389 benchmark instances comprehensively satisfy all evaluation and stress requirements.

---

## 2. Benchmark Audit & Instance Accounting

| Dataset Identifier | Physical Files Present | Original Instances | Adapted Instances | Successfully Validated | Source & Format |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `synthetic_manufacturing` | Native domain modules | 3 baseline presets | 3 baseline + 5 scalability + Disruption generator | 100% (All tested) | Python domain models (`app.sample_data`, `scalability_generator`) |
| `shift_scheduling` | 225 `.txt` + 225 `.xml` | 225 instances | 225 instances | 225 / 225 (100%) | `data/instances1_225/instances1_225/txt/*.txt` |
| `ptsp` | 137 `.dat` | 137 instances | 137 instances | 137 / 137 (100%) | `data/ptask/ptsp/*.dat` (Krishnamoorthy et al. 2012) |
| `nurse_rostering` | 24 `.txt` + 24 `.ros` | 24 instances | 24 instances | 24 / 24 (100%) | `data/instances1_24/instances1_24/*.txt` (Curtois & Qu 2014) |
| **Total** | **635 data files** | **389 instances** | **389 instances** | **100% compliant** | |

*Note: No missing files are reported as available instances. Every listed instance has a corresponding readable file on disk.*

---

## 3. Constraint Compatibility Audit & Fixes

### 3.1 Personnel Task Scheduling (PTSP)
- **Problem Audited:** In PTSP, tasks have continuous start and finish execution minutes (`start_m`, `end_m`). Multiple tasks can overlap on the continuous timeline.
- **Resolution:** The loader maps start/end minutes to normalized clock intervals (`HH:MM`). Pairwise temporal overlaps are strictly detected by `build_shift_conflict_pairs()` and enforced as hard packing constraints in MILP, Greedy, and ALNS schedulers:
  $$\sum_{j \in J} x_{ij s_1} + \sum_{j \in J} x_{ij s_2} \le 1 \quad \forall (s_1, s_2) \in C$$
- **Unsupported Constraints Explicitly Documented:** Task preemption/pausing (PTSP tasks are atomic) and continuous physical travel time between distant workstation cells.

### 3.2 Shift Scheduling (`instances1_225`)
- **Problem Audited:** Benchmark contains 15-minute time intervals, task cover minimum/maximum limits, and minimum working minute requirements (`MinTotalMinutes`).
- **Resolution:**
  - `SECTION_COVER` minimum staffing headcount is mapped to hard demand `required_headcount`.
  - Max limits in `SECTION_COVER` are unconstrained in MVP (Ordivanta enforces $\ge d_{js}$; recovery mode minimizes excess hours).
  - `MinTotalMinutes` and intra-shift break rules are explicitly labeled as unsupported rather than falsely claimed.

### 3.3 Nurse Rostering (`instances1_24`)
- **Problem Audited:** Hospital ward rostering contains consecutive shift bounds (`MinConsecutiveShifts`, `MaxConsecutiveShifts`), weekend limits, and soft preference penalties.
- **Resolution:**
  - `SECTION_DAYS_OFF` is directly enforced by removing unavailable shift IDs from `available_shifts`.
  - `MaxTotalMinutes` is mapped to employee `max_hours`.
  - Consecutive shift bounds, weekend caps, and soft penalties are documented as unsupported. No synthetic qualifications or salary grades are labeled as benchmark facts.

---

## 4. Synthetic Extension Layer Governance

In accordance with scientific integrity guidelines:
- **Zero Fabrication:** The raw benchmark files in `data/` remain 100% read-only and immutable.
- **Labeled Synthetic Extensions:** Features required for realism experiments (skill proficiency tiers 1–5, mandatory certifications, voluntary overtime opt-in consent, wage rates, and absenteeism shocks) are applied strictly via `ScenarioGenerationParams` and documented synthetic scenarios.
- Benchmark loaders never claim that `Instance1.txt` or `1_7_10_1.txt` contains native wages, overtime consent, or certifications.
