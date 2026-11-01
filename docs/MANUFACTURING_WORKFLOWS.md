# Manufacturing Operational Workflows

## 1. Schedule Lifecycle State Machine

```mermaid
stateDiagram-v2
    [*] --> DRAFT: Solver Generates Roster
    DRAFT --> DRAFT: Supervisor Adjustments & Replacements
    DRAFT --> PENDING_APPROVAL: Submit for Operations Review
    PENDING_APPROVAL --> DRAFT: Rejected (with Feedback)
    PENDING_APPROVAL --> APPROVED: Operations Manager Approves
    APPROVED --> PUBLISHED: Publish to Shop Floor (Horizon < Freeze Window)
    PUBLISHED --> DRAFT: Disruptive Shift Shock (Emergency Reroster)
    PUBLISHED --> SUPERSEDED: Replaced by New Version
    SUPERSEDED --> [*]
```

### State Definitions
- **`DRAFT`:** Working candidate schedule produced by MILP, Recovery MILP, or manual supervisor edits. Never exposed to floor workers.
- **`PENDING_APPROVAL`:** Frozen draft undergoing review by plant management.
- **`APPROVED`:** Authorized schedule verified by independent validation.
- **`PUBLISHED`:** Active shop-floor roster. Shift times and workstations are locked.
- **`SUPERSEDED`:** Historical revision archived for compliance and audit reporting.

---

## 2. Shift Disruption & Shortage Resolution Workflow

When a worker calls in sick or an unplanned absence occurs:

```mermaid
sequenceDiagram
    actor Supervisor
    participant System as Ordivanta Engine
    participant Policy as Plant Policy Engine
    participant Floor as Shop Floor Roster

    Floor->>Supervisor: Worker Absent (e.g. Emp_014)
    Supervisor->>System: Mark Employee Absent (Reason: Sick Leave)
    System->>Policy: Evaluate Replacement Eligibility
    Note over System,Policy: Filter: Qualified (Policy) + Available + Non-Conflicting Rest + Under Hours Cap
    System-->>Supervisor: Ranked Candidate Pool (Regular & Voluntary OT)
    Supervisor->>System: Confirm Replacement Assignment
    System->>Floor: Update Shift Roster & Log Audit Record
```

---

## 3. Worker State Distinctions
To maintain transparency and labor relations:
1. **Available:** Scheduled on regular shift window, qualified, not absent, and has available hours.
2. **Consenting Overtime Volunteer:** Has active opt-in consent on file, but must be confirmed before shift assignment.
3. **On-Call Candidate:** Available for call-in notification within minimum lead hours; assignment requires affirmative supervisor confirmation.
4. **Absent:** Excluded from all assignment eligibility for the duration of absence.
