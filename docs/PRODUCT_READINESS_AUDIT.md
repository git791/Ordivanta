# Product Readiness Audit: From Research Prototype to Commercial Enterprise

**Date:** 2026-11-01  
**Project:** Ordivanta Workforce Scheduling  

---

## 1. Executive Summary

Ordivanta has validated mathematical scheduling algorithms (Two-Stage MILP, Lexicographic Recovery MILP, Greedy baseline, and ALNS metaheuristic) with provable optimality reporting and independent validation.

To transition from a decision-support prototype into a commercial manufacturing product, the platform requires:
1. Operational plant policy management (replacing ad-hoc solver configs).
2. Explicit schedule revision lifecycles (`DRAFT` → `PENDING_APPROVAL` → `APPROVED` → `PUBLISHED` → `SUPERSEDED`).
3. Supervisor-centric operational views (specialist shortages, overtime consent tracking, replacement candidate matching).
4. Multi-tenant commercial security boundaries, audit trails, and data protection.

---

## 2. Current Architecture vs. Commercial Requirements

| Dimension | Current State | Commercial Requirement | Gap / Action |
| :--- | :--- | :--- | :--- |
| **Data Persistence** | SQLite (`aiosqlite`) single database file | Multi-tenant PostgreSQL with row-level security | Add plant-level tenant isolation, connection pooling, and automated schema migrations (Alembic). |
| **Authentication & RBAC** | Open endpoints (no auth tokens) | Role-Based Access Control (`Planner`, `Supervisor`, `Plant Manager`, `Auditor`) | Implement JWT/OAuth2 authentication with policy enforcement per endpoint. |
| **Plant Policies** | Embedded in API request DTOs (`ObjectiveConfig`) | Versioned server-side plant configuration entities | Centralized `PlantPolicy` schema and persistence layer. |
| **Schedule Workflow** | Solve output returned directly; immediately overwriteable | Formal state machine: `DRAFT` $\to$ `PENDING` $\to$ `APPROVED` $\to$ `PUBLISHED` | Versioned schedule drafts, supervisor approval gates, and revision diff tracking. |
| **Worker Overtime** | `overtime_opt_in` boolean on Employee | Formal consent records with expiry, opt-in tracking, and approval states | Distinguish willing candidates from confirmed roster assignments. |
| **Asynchronous Jobs** | Synchronous execution via `asyncio.to_thread` | Background task queues (Celery / Redis / RQ) | Decouple long-running MILP solves from HTTP request cycles with progress polling and webhook notifications. |
| **Audit Logging** | Ephemeral console logging | Tamper-evident operational audit logs | Log who approved overrides, published rosters, or modified shift policies. |

---

## 3. Operational Workflow Gaps Identified

1. **No Draft Approval Gate:** Schedulers currently produce immediate solved schedules. Supervisors cannot review, adjust, or request approvals before shift publication.
2. **Lack of Replacement Candidate Search:** When a worker is flagged absent, the system identifies shortages but does not provide supervisors with a ranked list of available, qualified, non-conflicting replacement staff.
3. **Overtime Consent Ambiguity:** Consent must not be confused with unconfirmed availability. An employee who consents to overtime must still have specific call-in shifts confirmed before publishing.

---

## 4. Implementation Priorities for Product Readiness

- **Priority 1:** Redesign Operations Dashboard for shift supervisors (KPIs, specialist bottlenecks, approval queues, real trend charts).
- **Priority 2:** Server-side versioned Plant Policy Engine.
- **Priority 3:** Schedule Lifecycle & Revision Management.
- **Priority 4:** Shortage & Overtime Replacement Candidate Workflows.
- **Priority 5:** Commercial Multi-tenant & Security Specifications.
