<!-- File path: docs/designs/regression_report.md -->

# Visual Intelligence Runtime (VIR) — Regression Report

This report outlines the visual regression testing capabilities, pixel comparison algorithms, and safety ignore mask controls built into the VIR sensory and memory layers.

---

## 1. Visual Comparison Engine

The comparison engine leverages Pillow to compute structural visual regression between active screenshots and established baselines.

- **Ignore Mask Bounds**: Regions specified as `(x, y, w, h)` are dynamically overridden with black pixels on both compared images before the comparison logic runs, avoiding false positives on dynamic areas (e.g. usernames, clocks).
- **Pixel Difference Threshold**: Color differences with R+G+B sum exceeding 10 are counted as visual regression.

---

## 2. Regression Database Mappings

| Method | Database Table | Actions |
| :--- | :--- | :--- |
| `get_active_baseline` | `vir_baselines` | Reads historical baseline binary data matching feature routes and viewports |
| `promote_new_baseline` | `vir_baselines` | Inserts or replaces active baseline binaries with current screenshots |
| `clear_expired_baselines` | `vir_baselines` | Deletes records older than configured timestamps to control DB growth |

---

## 3. Regression Test Executions
- `test_pixel_comparer.py`: Verifies difference ratios and ignore masks. (PASS)
- `test_baselines.py`: Verifies promotion lifecycle and database persistence. (PASS)
