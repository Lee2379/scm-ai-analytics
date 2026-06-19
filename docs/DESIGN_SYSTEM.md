# SCM Analytical Workspace Design System

## Product intent

The interface is a decision-science workspace for SCM analysts and managers. It should read as an operational analytics product, not a marketing page or a generic Streamlit demo.

## Layout

- Desktop reference viewport: 1440 × 1024.
- Left rail: analysis navigation and data context.
- Main canvas: status, global filters, KPI strip, diagnostic charts, and action tables.
- Right rail: persistent SCM Decision Copilot with grounded suggested questions.
- Responsive behavior: below 980px, the copilot returns to normal document flow.

## Visual tokens

- Critical/active red: `#e60012`.
- Primary ink: `#171717`.
- Secondary text: `#6b6f76`.
- Divider: `#e3e5e8`.
- Soft surface: `#f7f8f9`.
- Base surface: white.
- Corners: 3–4px; avoid pill cards and excessive rounding.
- Shadows: only the persistent copilot may use subtle elevation.

## Interaction rules

- Global city and inventory-status filters update headline metrics and supported detail views.
- Sidebar navigation switches one analytical workspace at a time.
- Copilot prompt suggestions execute real local agent queries.
- Red is reserved for active navigation, stockout risk, priority actions, and primary controls.

## Content rules

- Keep the 28-day horizon, data freshness, metric grain, and simulation caveats visible.
- Prefer diagnostic labels and decision rationale over decorative explanatory copy.
- Do not add ontology graphics, marketing heroes, decorative grids, gradients, or nested card stacks.
