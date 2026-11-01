# Plant Policy Specification

## 1. Overview
The Plant Policy Engine centralizes manufacturing operational rules, shift boundaries, and qualification enforcement. Rather than requiring planners to configure mathematical solver weights manually, operations managers set declared policies that are translated server-side into optimizer constraints and validator rules.

---

## 2. Policy Model (`PlantPolicy`)

```json
{
  "policy_id": "policy_mfg_std_v1",
  "plant_id": "plant_detroit_01",
  "name": "Standard Automotive Assembly Policy 2026",
  "version": 1,
  "is_active": true,
  "working_hours": {
    "regular_hours_limit": 40.0,
    "max_overtime_hours": 10.0,
    "require_overtime_consent": true,
    "min_rest_hours_between_shifts": 11.0,
    "max_consecutive_days": 6
  },
  "qualification": {
    "default_policy": "LEVEL_AND_CERTIFICATION",
    "enforce_proficiency_levels": true,
    "enforce_certifications": true,
    "allow_provisional_supervision": false
  },
  "labor_cost": {
    "currency": "USD",
    "default_base_rate": 28.50,
    "overtime_premium_multiplier": 0.50,
    "weekend_shift_differential": 3.00,
    "night_shift_differential": 4.50
  },
  "call_in_and_on_call": {
    "min_call_in_notice_hours": 4.0,
    "require_supervisor_confirmation": true
  },
  "lifecycle_governance": {
    "require_manager_approval_to_publish": true,
    "freeze_horizon_hours": 24.0
  }
}
```

---

## 3. Server-Side Enforcement Rules

1. **Working Hours & Overtime:**
   - If `require_overtime_consent` is `true`, an employee with `overtime_opt_in == false` cannot be assigned $> \text{regular\_hours\_limit}$ hours under any circumstances.
   - If total assigned hours exceed $\text{regular\_hours\_limit} + \text{max\_overtime\_hours}$, the validator flags `HOURS_EXCEEDED` and `OVERTIME_CAP_EXCEEDED`.

2. **Temporal Rest:**
   - Any pair of shifts with an inter-shift rest period $< \text{min\_rest\_hours\_between\_shifts}$ is prohibited by both the optimizer's conflict graph and the independent validator.

3. **Qualification:**
   - Enforces `LEVEL_AND_CERTIFICATION` across all operational cells unless explicitly relaxed by an authorized plant override.

4. **Neutral Jurisdictional Phrasing:**
   - Rules are modeled as contractual plant policies (e.g. "Configured 11-hour rest policy") rather than hardcoded statutory claims ("EU Working Time Directive").
