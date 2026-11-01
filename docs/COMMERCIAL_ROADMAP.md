# Commercialization Roadmap: Enterprise Manufacturing Readiness

This roadmap outlines the milestones, architectural foundations, and integration boundaries required before deploying Ordivanta in production manufacturing plants.

---

## 1. Security, Multi-Tenancy & Data Protection

### 1.1 Multi-Tenant Plant Isolation
- **Organization Hierarchy:** `Enterprise` $\to$ `Facility / Plant` $\to$ `Production Line / Cell`.
- **Database Partitioning:** Row-Level Security (RLS) on PostgreSQL matching `plant_id`. Cross-plant visibility is restricted to enterprise directors.

### 1.2 Role-Based Access Control (RBAC)
| Role | Capabilities |
| :--- | :--- |
| **Shift Supervisor** | View published schedules, report worker absenteeism, review replacement candidate recommendations, assign approved on-call staff. |
| **Plant Planner** | Create scenarios, configure plant policies, execute optimizers, modify drafts, submit schedules for approval. |
| **Operations Manager** | Approve/reject schedule drafts, authorize overtime caps, publish schedules, review labor cost variance. |
| **Compliance Auditor** | Read-only access to version history, audit logs, and independent validation reports. |

### 1.3 Employee Privacy & Data Protection (GDPR / CCPA)
- Employee PII (names, phone numbers, wage contracts) is encrypted at rest using AES-256.
- Solver models operate on pseudonymized tokens (`emp_014`, `skill_welding_3`), decoupling optimization logs from sensitive worker profiles.
- Absence reasons are categorized into neutral operational codes (e.g. `UNPLANNED_MEDICAL`, `STATUTORY_LEAVE`) without storing health details.

---

## 2. Infrastructure & Operations

### 2.1 Asynchronous Optimization Job Queue
- Decouple MILP solving from HTTP request threads using **Celery + Redis**.
- Provides real-time job progress polling, cancellation tokens, and worker execution time limits.

### 2.2 Logging & Observability
- Structured JSON logging with OpenTelemetry tracing across API, optimizer, and validator.
- Automated Prometheus metrics tracking solver gap, runtime seconds, coverage rate, and validation error counts.

### 2.3 Disaster Recovery & Backup
- Automated point-in-time recovery (PITR) with continuous write-ahead logging (WAL) for PostgreSQL.
- Deterministic random seed persistence guaranteeing exact replay of historical schedule generation.

---

## 3. Integration Boundaries (HRMS, Time & Attendance, ERP)

```
[HRMS / Workday / SAP] ---> Ingest Workers, Skills, Certifications & Rates
                                     │
                                     ▼
                          [ Ordivanta Engine ]
                                     │
                                     ▼
[Shop Floor Displays] <--- Export Approved & Published Roster (ICS/CSV/REST)
                                     │
                                     ▼
[Payroll Engine] <--- Transmit Actual Scheduled Hours & Overtime Premiums
```

---

## 4. Factory Pilot Checklist

Before initiating an on-site factory pilot:
- [ ] Connect plant-specific skill matrix and certification expiration tracker.
- [ ] Align plant overtime policy with local collective bargaining agreements.
- [ ] Run dry-run historical comparisons on 4 weeks of past factory rosters.
- [ ] Train shift supervisors on draft review and replacement candidate approval flows.
- [ ] Verify zero data leakage across multi-plant test environments.
