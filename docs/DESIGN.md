# Design System — Ordivanta
## Industrial operations control room

## 1. Design direction

Ordivanta should feel like a dependable manufacturing planning console: precise, calm, information-dense and operational. The interface should help a supervisor answer four questions quickly:

1. Is the staffing plan complete?
2. Where are the shortages or conflicts?
3. How is work distributed?
4. Can this result be trusted and reviewed?

Use a **modern industrial utility** style rather than a flashy SaaS landing-page aesthetic. Prioritise structured grids, restrained colour, high legibility, strong table design and meaningful status messages. Avoid neon, glassmorphism, oversized gradients, decorative motion and emoji-heavy controls.

The palette and information hierarchy are design recommendations informed by IBM's restrained neutral-plus-blue system and dashboard guidance favouring consistent grey surfaces, contrasting content panels and accessible data colours. This is not an official IBM or Michelin-branded product.

## 2. Colour palette

### Core tokens

| Token | Hex | Use |
|---|---|---|
| `--canvas` | `#F3F5F7` | App background |
| `--surface` | `#FFFFFF` | Cards, tables, forms |
| `--surface-muted` | `#E9EEF2` | Secondary panels and table headers |
| `--ink` | `#17212B` | Primary text |
| `--ink-muted` | `#536171` | Secondary text |
| `--border` | `#D4DCE3` | Dividers and control borders |
| `--primary` | `#245A81` | Primary actions, selected navigation |
| `--primary-hover` | `#1B4667` | Hover/pressed action |
| `--primary-soft` | `#E4EEF5` | Selected rows and subtle emphasis |
| `--steel` | `#667B8D` | Secondary iconography and metadata |
| `--success` | `#276749` | Validated / complete |
| `--success-soft` | `#E5F3EB` | Success backgrounds |
| `--warning` | `#8A5A13` | Warning / near limit |
| `--warning-soft` | `#FFF3D8` | Warning backgrounds |
| `--danger` | `#A33131` | Infeasible / blocking error |
| `--danger-soft` | `#FBEAEA` | Error backgrounds |
| `--info` | `#315E83` | Informational messages |

### Palette principles
- Use white and cool grey as the dominant surfaces; blue is an action and focus accent, not a background for everything.
- Use semantic status colours only for actual states.
- Pair every status colour with a label and, where appropriate, an icon or shape.
- Check text/background contrast in the rendered interface. Do not assume a colour pair passes contrast because it looks readable.
- Avoid gradients and neon cyan/lime/purple.
- Charts should use a restrained, repeatable series palette and provide labels/tooltips; never rely on colour alone.

## 3. Typography

### Recommended font stack
- **Primary UI:** IBM Plex Sans.
- **Numeric / tabular data:** IBM Plex Mono for IDs, run times and tightly aligned numerical columns; use tabular numerals.
- **Fallback:** `Inter, ui-sans-serif, system-ui, sans-serif` for UI; `ui-monospace, SFMono-Regular, Menlo, monospace` for technical data.

IBM Plex Sans is a strong fit for technical operations interfaces; IBM's technical diagram guidance also specifies it. If self-hosting fonts, use licensed webfont files and keep a robust system fallback.

### Type scale
| Token | Size / line-height | Weight | Use |
|---|---|---|---|
| `text-xs` | 12 / 16 px | 400–500 | Table metadata, timestamps |
| `text-sm` | 14 / 20 px | 400–500 | Dense UI, helper text |
| `text-base` | 16 / 24 px | 400 | Standard body and controls |
| `text-lg` | 18 / 28 px | 500–600 | Section titles |
| `text-xl` | 20 / 28 px | 600 | Page section heading |
| `text-2xl` | 24 / 32 px | 600 | Page title |
| `text-3xl` | 30 / 36 px | 600 | Dashboard headline only when useful |

Avoid long all-caps labels. Use sentence case; reserve uppercase for short technical abbreviations.

## 4. Layout and spacing

- Desktop-first, responsive down to tablet widths.
- Sidebar: approximately 232–248 px on wide screens; collapsible on smaller screens.
- Main content: fluid, with a readable maximum width for forms and a wide canvas for schedule tables.
- Use a 4 px base spacing unit and an 8 px primary rhythm.
- Page padding: 24–32 px desktop, 16 px tablet.
- Card padding: 16–20 px.
- Use 1 px borders and modest 6–10 px corner radii. Avoid excessive pill shapes.
- Prefer crisp panels over large floating shadows.
- Tables should support sticky headers, row hover, clear alignment and horizontal scrolling when necessary.

## 5. Component style

### Navigation
- Dark ink or neutral sidebar, white/soft-neutral active item with a blue left rail or icon.
- Labels: Dashboard, Workforce, Production Units, Shift Demand, Schedule Runs, Experiments, Settings.
- Active state must be understandable without colour alone.

### KPI cards
Show meaningful operational metrics:
- Required positions
- Filled positions / coverage
- Validation violations
- Scheduled hours
- Latest solver status
- Solve time

Each metric must include a clear label, value, and contextual note. Do not display made-up performance claims.

### Tables
- Use compact but comfortable row heights (roughly 44–52 px).
- Align numerical columns consistently.
- Keep employee and unit names left-aligned.
- Use small status labels with text.
- Provide filters and empty states.
- Do not overload each row with icons.

### Status states
- `OPTIMAL`: “Optimal solution found”
- `FEASIBLE`: “Feasible solution — optimality not proven”
- `INFEASIBLE`: “No schedule satisfies the current hard constraints”
- `NOT_SOLVED`: “No usable solution returned”
- `ERROR`: “Solver error — check configuration”

Status wording must match the actual solver adapter. Include explanatory details and next steps.

### Charts
- Coverage: horizontal bars or compact progress bars by unit/shift.
- Workload: sorted horizontal bars by employee.
- Algorithm comparison: grouped bars for comparable metrics; show runtime and status separately.
- Provide accessible labels and tabular alternatives for important data.

## 6. Main page structure

### Dashboard
- Top bar with page title, active scenario selector and “New schedule run” action.
- Four or five KPI cards.
- Coverage-by-shift chart.
- Recent schedule runs table.
- Blocking issues panel with direct links to the relevant input.

### Schedule builder
Use a stepper:
1. Scenario and planning horizon
2. Workforce and availability
3. Unit demand
4. Algorithm and objective
5. Review inputs
6. Run schedule

Show a final summary of employee count, unit count, shifts and total required positions before solving.

### Schedule results
- Header with run ID, algorithm, solver status and timestamp.
- Coverage summary and validation summary.
- Filters for shift, unit and employee.
- Roster table.
- Workload distribution panel.
- Unfilled demand / violations panel.
- Export button only when permitted by the run state.

### Experiments
- Scenario selector.
- Algorithm comparison table.
- Shared-input confirmation.
- Runtime, coverage, hard violations and configured objective value.
- Methodology notes and download of results.

## 7. Interaction and motion

- Use immediate feedback for form validation.
- Use a restrained loading state while solving; show that a solve is running, not a fake percentage.
- Respect `prefers-reduced-motion`.
- Use subtle 120–180 ms transitions for hover/focus only.
- Never hide errors behind transient toast notifications alone.
- Confirm destructive actions such as deleting a scenario.
- Keep keyboard focus visible.

## 8. Accessibility checklist

- Semantic heading order and labelled form fields.
- Keyboard-operable navigation, menus and tables.
- Visible focus rings.
- Sufficient contrast, especially for muted text and status chips.
- Text labels and icons in addition to status colours.
- Charts with accessible descriptions or table equivalents.
- No meaning conveyed only by red/green.
- Test at 200% zoom and narrower viewports.

## 9. Example CSS tokens

```css
:root {
  --canvas: #F3F5F7;
  --surface: #FFFFFF;
  --surface-muted: #E9EEF2;
  --ink: #17212B;
  --ink-muted: #536171;
  --border: #D4DCE3;
  --primary: #245A81;
  --primary-hover: #1B4667;
  --primary-soft: #E4EEF5;
  --success: #276749;
  --success-soft: #E5F3EB;
  --warning: #8A5A13;
  --warning-soft: #FFF3D8;
  --danger: #A33131;
  --danger-soft: #FBEAEA;
}
```

## 10. Design rationale and references

- IBM Design Language — Color: https://www.ibm.com/design/language/color/
- IBM Design Language — Technical diagrams (typography and accessible diagram colour): https://www.ibm.com/design/language/infographics/technical-diagrams/design/
- Michelin Design System — Dashboard principles: https://designsystem.michelin.com/data-visualization/design-guidelines/principles-of-a-dashboard

These sources inform the direction; the tokens above are a project-specific palette and should be contrast-tested in the final UI.
