# webpconverter

A macOS CLI tool that scans a project's asset folder and converts PNG and JPEG images to optimized WebP — combining fast load times with excellent visual quality.

## Features

- Recursively discovers `.png`, `.jpg`, and `.jpeg` files
- Skips any `optimized/` folders (never re-processes already converted files)
- Two-step workflow: **plan first, then execute** — review before committing
- Saves converted files in an `optimized/` subfolder beside the originals
- Generates a `convert_report.md` with output paths ready to paste into an AI for bulk reference updates

## Installation

Requires Python 3.9+ and [pipx](https://pipx.pypa.io/stable/).

```bash
# Install the tool globally via pipx
pipx install /path/to/webp-converter

# Verify
webpconverter --version
```

> **Note:** Plan files created before SVG support was removed may still list `.svg` paths in the YAML front-matter. Regenerate the plan with `webpconverter plan` or remove those entries before running `webpconverter exec`.

### Development install (editable)

```bash
git clone https://github.com/YOUR_USERNAME/webp-converter.git
cd webp-converter
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
```

---

## Usage

### 1. Generate a conversion plan

```bash
# Scan the current directory (default)
webpconverter plan

# Scan a specific assets folder
webpconverter plan --dir src/assets

# Custom quality (1–100, default 85)
webpconverter plan --dir src/assets --quality 80

# Write the plan file somewhere specific
webpconverter plan --dir src/assets --output-dir /tmp
```

This produces a timestamped plan file such as `plan_20260422_153000.md`:

```
## webpconverter plan — 2026-04-22 15:30:00

> 11 files scanned — total original: 1.4 MB — estimated after: 980.0 KB — estimated saving: 30.0%
> WebP quality setting: 85

| # | File                      | Type | Current Size | Est. WebP Size | Est. Saving | Est. Load Gain |
|---|---------------------------|------|-------------|----------------|-------------|----------------|
| 1 | `src/assets/logo.png`     | PNG  | 120.0 KB    | 84.0 KB        | 30.0%       | 0.3 ms         |
| 2 | `src/assets/hero.jpg`     | JPEG | 320.0 KB    | 240.0 KB       | 25.0%       | 0.6 ms         |
| 3 | `src/assets/banner.jpg`   | JPEG | 256.0 KB    | 192.0 KB       | 25.0%       | 0.5 ms         |
```

You can edit the plan (remove rows, change the quality in the front-matter) before executing.

### 2. Execute the plan

```bash
webpconverter exec plan_20260422_153000.md
```

Each source file is converted and saved into an `optimized/` subfolder:

```
src/assets/logo.png
src/assets/optimized/logo.webp   ← output here

src/assets/images/hero.jpg
src/assets/images/optimized/hero.webp
```

After conversion a `convert_report.md` is written next to the plan file:

```
## webpconverter report — 2026-04-22 15:31:45

> Plan file: plan_20260422_153000.md
> WebP quality: 85
> Results: 11 converted, 0 failed out of 11 total
> Total size before: 1.4 MB → after: 980.0 KB — saved 420.0 KB (30.0%)

### Output paths (for AI reference)
/Users/you/project/src/assets/optimized/logo.webp
/Users/you/project/src/assets/optimized/hero.webp
...
```

Paste the **Output paths** block into your AI assistant to automatically update all asset references in your project.

---

## WebP quality guide


| Quality | Use case                                  | Typical saving vs PNG |
| ------- | ----------------------------------------- | --------------------- |
| 90–100  | Lossless-like, maximum fidelity           | ~15–20%               |
| **85**  | **Default — excellent quality, web-safe** | ~25–35%               |
| 75–84   | Good quality, noticeable file reduction   | ~35–45%               |
| 60–74   | Acceptable, high compression              | ~50–60%               |


---

## How it works

```
webpconverter plan
    └─ scanner.py    → discover assets
    └─ estimator.py  → size/saving estimates
    └─ planner.py    → write plan_*.md

webpconverter exec plan_*.md
    └─ planner.py    → parse YAML front-matter
    └─ converter.py  → Pillow (PNG/JPEG) → WebP
    └─ reporter.py   → write convert_report.md
```

## Dependencies


| Package    | Purpose                        |
| ---------- | ------------------------------ |
| `Pillow`   | PNG / JPEG → WebP              |
| `click`    | CLI framework                  |
| `rich`     | Terminal progress & tables     |
| `PyYAML`   | Plan file front-matter parsing |


