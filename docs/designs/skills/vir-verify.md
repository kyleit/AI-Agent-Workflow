# Skill Specification — vir-verify

This skill specifies the visual audit, design token verification, and quality gate evaluations.

---

## 1. Metadata Frontmatter
- **Name**: `vir-verify`
- **Description**: Visual regression testing, design token compliance audits, and accessibility validation gates.
- **Version**: `1.0.0`

---

## 2. Core Specification

### Purpose
Audit page screenshots and DOM layouts matching guidelines tokens and WCAG thresholds rules.

### Required Inputs
- `screenshot`: Current screenshot PNG bytes array.
- `baseline`: Target baseline PNG bytes array.
- `tokens`: Configured design tokens object.
- `a11y_rules`: Axe-core standard WCAG guidelines.

### Produced Outputs
- `evidence`: Standard Evidence structures containing found violations.
- `consensus`: Combined consensus score and quality gate verdict (PASS/FAIL).

---

## 3. Invocation & Execution Rules

### Allowed Actions
- Invoking pixel difference matchers.
- Parsing CSS/Tailwind elements style attributes.
- Dispatching VETO events on the event bus when MUST rules are violated.

### Forbidden Actions
- Directly changing source code style attributes to force compliance.
- Modifying SQLite baselines histories without explicit promote commands.

### Required Runtime APIs
- `vir.runtime.vision.compare_pixels(curr, base, ignore_masks)`
- `vir.runtime.bus.publish(event)`
