# Design System

## Direction

A modern engineering workbench: dense, quiet, and explicit. Open-PHA informs the
worksheet-first information architecture, while PreventA replaces legacy toolbar
clutter with labeled actions, stable navigation, strong selection states, and a
source-aware assistance panel.

## Color

Use a restrained light strategy. The background is pure white; brand color appears
only in navigation selection, primary actions, focus-adjacent states, and evidence
confirmation.

```css
--color-bg: oklch(1 0 0);
--color-surface: oklch(0.972 0.004 120);
--color-surface-strong: oklch(0.935 0.007 120);
--color-ink: oklch(0.19 0.012 120);
--color-muted: oklch(0.47 0.014 120);
--color-primary: oklch(0.36 0.071 120);
--color-primary-soft: oklch(0.93 0.035 120);
--color-warning: oklch(0.72 0.15 78);
--color-danger: oklch(0.56 0.19 28);
--color-success: oklch(0.53 0.13 145);
--color-info: oklch(0.54 0.13 250);
```

## Typography

Use `Inter` where available with a Segoe UI/system fallback. UI hierarchy uses a
fixed product scale: 0.75rem metadata, 0.8125rem compact controls, 0.875rem table
content, 1rem body, 1.125rem panel headings, and 1.375rem page titles. Use a
monospace stack for PFD, SIL, frequencies, and aligned numeric values.

## Layout

- Desktop shell: 64px application rail, 248px study navigator, fluid worksheet,
  336px evidence panel.
- Keep study context and worksheet actions sticky.
- Use 4px-based spacing tokens with compact 8px and 12px grouping.
- Cards are reserved for independently actionable evidence candidates. Worksheet and
  navigation groups use dividers and background layers instead.
- Below 1180px, evidence becomes an overlay drawer. Below 860px, study navigation
  becomes a drawer and the worksheet receives horizontal scrolling.

## Components

- Buttons use 8px radius, explicit verb labels, and 44px touch targets when pointer is
  coarse.
- Inputs use visible labels where standalone; table cells may use contextual column
  headers and accessible names.
- Risk badges combine text, shape, and color.
- Source citations use compact neutral chips with full references available in title
  text.
- Selected table cells use a 2px primary inset ring; selected rows use a subtle
  primary-tinted surface.
- Toasts confirm autosave, report generation, and suggestion insertion.

## Motion

Use 160-220ms ease-out transitions for drawers, selection, and feedback. Avoid page
load choreography. Reduced-motion users receive instant state changes.

