# capstone-labmate v1.0.0-beta

[English](README.md) ·  `中文`

> 一个本地优先、开源的 AI 技能包，帮助师生处理 PASCO Capstone（`.cap`）实验数据——所有解析与处理均在本地完成，确保数据隐私。

---
**寻找集成生态？**
本仓库为独立模块。如需体验包含四层确定性调度架构的完整跨平台插件套件，请访问集成版仓库：[**Chelate Shell (螯合壳)**](https://github.com/JiamingShi-JsPhys/chelate-shell)。

> **免责声明**：本项目为独立的第三方开源互操作性教学辅助工具，与 PASCO Scientific 公司无任何附属、背书或赞助关系。"PASCO" 与 "Capstone" 为其各自所有者的注册商标。本工具所有数据处理均在本地完成；使用者需自行确保使用本工具符合所在学校的学术诚信规范。
>
> **Disclaimer**: This is an independent, open-source, third-party tool for interoperability and educational assistance. It is not affiliated with, endorsed by, or sponsored by PASCO Scientific. "PASCO" and "Capstone" are registered trademarks of their respective owners. All processing runs locally; users are responsible for complying with their institution's academic-integrity policy.

>除此之外，本仓库包含作者为自动化科研工作流而开发的辅助工具。它不是经过同行评审的学术项目。部分样板代码或实用脚本可能在 AI 辅助下生成，并经过作者高层面的审查与修改整合。作者对任何第三方代码问题不承担责任，但承诺及时处理任何合理的诉求。
---

## 它能做什么 (Workflow)

`capstone-labmate` 将繁琐的实验流程自动化为三个标准阶段：

1. **课前预制 (Pre-Lab)**：将老师的实验手册（PDF/docx）放入工作区并唤醒技能。它会自动读取手册，生成一份 **`.cap` 模板**（包含采样频率、数据列、预置公式、图表与坐标轴）。若目标列未被注册为数据列，坐标轴绑定会回退为零 GUID 自动选择，manifest 里的 `axes_bound` 字段会如实标记哪些轴需要你在 Capstone 里手动连线。
2. **课中采集 (In-Lab)**：学生在预设好的 `.cap` 模板上连接硬件进行正式实验（**纯人工操作，AI 物理隔离**），完成后另存为最终数据文件。
3. **课后报告 (Post-Lab)**：唤醒技能并下达“生成实验报告”指令。工具会在本地进行降采样、导出 CSV 供 Excel 筛查，由宿主大模型（LLM）根据模板生成图文并茂的报告草稿。**每个数值均可溯源**；弱信号或未观测项必须经过数据筛查与局部放大截图确认。

## 面向谁 (Target Audience)

*   **教师 / 助教**：课前一键生成模板；课后批量清洗数据、生成分析草稿，大幅降低备课与批改负担。
*   **学生 / 学习者**：免除手动画图与降采样的折磨，聚焦物理现象思考。草稿需自行核对并得出结论。
*   **AI 开发者**：基于 Agent-Native 架构，支持无缝挂载至 Claude Code、DeepSeek Harness、OpenAI Codex、WorkBuddy 等主流框架。

## 预置配置 (Predefined Profiles)

随包附带 **6 个采样配置**（`config/sampling_profiles.json`）：`blackbody`、`voltmeter`、`pendulum`、`uniform_motion`、`freefall`、`ohms_law`、`hooke`。每个配置包含采样频率、数据列、预置公式、图表与坐标轴。用 `--profile <name>` 指定其一，或由工具从实验手册自动推断最匹配的配置。

若未提供 base `.cap` 模板，工具会自动回退到内置的 **`assets/blank.base.cap`**，Pre-Lab 阶段可独立运行。

## 快速开始 (Quick Start)

**方式一：跨平台安装器（推荐小白使用）**
前往 [Releases](https://github.com/JiamingShi-JsPhys/capstone-labmate/releases) 页面，下载最新的安装包（`.exe`）。双击运行后，勾选你正在使用的 AI 宿主（如 WorkBuddy、Claude Code），点击安装即可自动配置环境。

**方式二：Windows 一键脚本**
打开 PowerShell 运行以下命令，自动下载并安装：
```powershell
irm https://raw.githubusercontent.com/JiamingShi-JsPhys/capstone-labmate/main/install-web.ps1 | iex
```

**方式三：手动安装（开发者）**
```bash
# 克隆仓库到本地 skills 目录
git clone https://github.com/JiamingShi-JsPhys/capstone-labmate.git ~/.workbuddy/skills/capstone-labmate

# 安装可选依赖（缺失时工具会自动降级，不阻塞运行）
pip install numpy matplotlib pypdf
```

> 完整流程说明、出厂校验清单与安全护栏，请阅读 [`SKILL.md`](SKILL.md)。

## 学术诚信红线 (Academic Integrity)

本工具**绝不代替你完成实验**。数据必须由学生在实验室人工采集，AI 在课中阶段绝对物理隔离。生成的内容仅为**数据分析草稿**，且每份草稿末尾强制附带不可删除的学术诚信水印。使用者必须遵守所在学校的学术规范。

## 协议与作者 (License & Author)

- **License**: [MIT](LICENSE)
- **Author & Maintainer**: Jiaming Shi (Westlake University)

## 报告问题

首选：在本仓库的 **Issues** 页面提交问题（对于安全漏洞问题的报告，使用备选方案）。

备选（仅供报告安全漏洞问题）：发送邮件至 `jiamingshi_git@outlook.com`

- **邮件主题**：必须包含前缀 `agent-skill_report`，并注明具体技能与简要问题。
  - 示例：`agent-skill_report capstone-labmate: path traversal 可读取任务文件夹之外的路径`
- **邮件正文**：必须包含复现步骤、预期行为、实际行为以及运行环境（操作系统、Python 版本、相关依赖安装状态）。
- 针对「文件丢失或损坏」的严重报告，请附带前后目录树结构（`tree` 输出）与生成的 `verification_report.md`。
- 提交清晰、可复现 Issue 或 Pull Request 的贡献者，将被列入下个版本发布说明的致谢名单。
