# capstone-labmate v1.0.0-beta

`English` · [中文](README_zh.md)

> A local-first, open-source AI skill pack that helps teachers and students work with PASCO Capstone (`.cap`) lab data—all parsing and processing run locally to protect data privacy.

---

> **Disclaimer**: This is an independent, open-source, third-party tool for interoperability and educational assistance. It is not affiliated with, endorsed by, or sponsored by PASCO Scientific. "PASCO" and "Capstone" are registered trademarks of their respective owners. All processing runs locally; users are responsible for complying with their institution's academic-integrity policy.

> Be the way, this repository contains auxiliary tools developed by the author to automate research workflows. It is not a peer-reviewed academic project. Some boilerplate or utility scripts may have been generated with the assistance of AI, and have been integrated with high-level review and modifications by the author. The author assumes no responsibility for any third-party code issues, but commits to promptly addressing any valid claims.


---

## What It Does (Workflow)

`capstone-labmate` turns tedious lab workflows into three standard stages:

1. **Pre-Lab**: Place the instructor's lab manual (PDF/docx) in the workspace and invoke the skill. It automatically reads the manual and generates a **`.cap` template** (including sampling rate, data columns, preset formulas, graphs, and axes). Axis binding falls back to a zero-GUID auto-select when the target column is not a registered data column; the manifest flags `axes_bound` so you know which axes need manual wiring in Capstone.
2. **In-Lab**: Students connect the hardware and conduct the actual experiment using the preconfigured `.cap` template (**purely manual operation; AI is physically isolated**). When finished, they save the final data file separately.
3. **Post-Lab**: Invoke the skill and issue the command "generate lab report." The tool performs downsampling locally and exports CSV files for Excel-based screening. The host LLM then generates an illustrated report draft based on the template. **Every value is traceable**; weak signals or unobserved items must be confirmed through data screening and zoomed-in screenshots.

## Who It's For

* **Teachers / Teaching Assistants**: Generate templates with one click before class; batch-clean data and generate analysis drafts after class, greatly reducing preparation and grading workload.
* **Students / Learners**: Skip the grind of manual plotting and downsampling and focus on thinking about the physics. Drafts must still be checked and conclusions drawn by the user.
* **AI Developers**: Built on an Agent-Native architecture and can be seamlessly mounted into mainstream frameworks such as Claude Code, DeepSeek Harness, OpenAI Codex, and WorkBuddy.

## Predefined Profiles

Ships with **6 sampling profiles** out of the box (`config/sampling_profiles.json`): `blackbody`, `voltmeter`, `pendulum`, `uniform_motion`, `freefall`, `ohms_law`, and `hooke`. Each bundles sampling rate, data columns, preset formulas, graphs, and axes. Run Pre-Lab with `--profile <name>` to pick one, or let the tool infer the closest match from the lab manual.

If no base `.cap` template is available, the tool falls back to the bundled **`assets/blank.base.cap`**, so the Pre-Lab stage works standalone.

## Quick Start

**Option 1: Cross-platform installer (recommended for non-technical users)**

Go to the [Releases](https://github.com/JiamingShi-JsPhys/capstone-labmate/releases) page and download the latest installer (`.exe`). Double-click to run it, select the AI host you are using (e.g., WorkBuddy or Claude Code), and click Install to configure the environment automatically.

**Option 2: Windows one-click script**

Open PowerShell and run the following command to download and install automatically:
```powershell
irm https://raw.githubusercontent.com/JiamingShi-JsPhys/capstone-labmate/main/install-web.ps1 | iex
```

**Option 3: Manual installation (developers)**
```bash
# Clone the repository into your local skills directory
git clone https://github.com/JiamingShi-JsPhys/capstone-labmate.git ~/.workbuddy/skills/capstone-labmate

# Install optional dependencies (the tool degrades gracefully if they are missing and will not block execution)
pip install numpy matplotlib pypdf
```

> For the full workflow, factory validation checklist, and safety guardrails, please read [`SKILL.md`](SKILL.md).

## Academic Integrity

This tool **will never do the experiment for you**. Data must be collected manually by students in the lab; AI is absolutely physically isolated during the in-lab stage. Generated content is only a **data-analysis draft**, and every draft is required to carry a non-removable academic-integrity watermark at the end. Users must comply with their institution's academic-integrity policies.

## License & Author

- **License**: [MIT](LICENSE)
- **Author & Maintainer**: Jiaming Shi (Westlake University)

## Report issues

Preferred: Open an issue on the repository's **Issues** page. For security-vulnerability reports, use the alternative channel below.

Alternative (security-vulnerability reports only): Send an email to `jiamingshi_git@outlook.com`.

- **Subject**: Must include the prefix `agent-skill_report`, the specific skill name, and a brief description.
  - Example: `agent-skill_report capstone-labmate: path traversal allows reading outside the task folder`
- **Body**: Must include reproduction steps, expected behavior, actual behavior, and the runtime environment (OS, Python version, relevant dependencies installed).
- For severe reports like "file lost or corrupted", attach the before/after directory tree (`tree` output) and the generated `verification_report.md`.
- Contributors who submit clear, reproducible issues or pull requests will be listed in the acknowledgements of the next release notes.
