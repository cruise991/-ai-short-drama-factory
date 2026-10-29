# GitHub 仓库备份状态审查与全量改动备份计划

> **生成时间**：2026-10-20  
> **审查分支**：`feature/web-dance-studio`  
> **远端配置**：
> - `origin`: `https://github.com/cruise991/ai-short-drama.git` (私有主开发/灾备仓库)  
> - `opensource`: `https://github.com/cruise991/-ai-short-drama-factory.git` (公开开源仓库)

---

## 一、当前 GitHub 备份与同步现状

1. **分支基线对比**：
   - 本地 `feature/web-dance-studio` 最新 Commit 为 `9531f3e`（docs: add comprehensive devops and backup operations manual）；
   - 与私有远端 `origin/feature/web-dance-studio` 处于完全对齐状态（0 Commit 领先，0 Commit 落后）。
2. **工作区未提交改动统计**：
   - **已修改文件（Modified）**：52 项
   - **未跟踪新文件（Untracked）**：104 项
   - **改动总计**：156 项
3. **安全与合规预检（Preflight Security Audit）**：
   - **敏感凭证检查**：经正则扫描，未跟踪及修改的代码中 **0 处 API Key / Token 泄露**；`.env` 和私有数据库被 `.gitignore` 严格拦截；
   - **大文件检查**：无任何未忽略的 >50MB 媒体二进制大文件；
   - **工作区杂物清理**：已更新 `.gitignore`，将 `debug_*/`、`debug_*.png`、`analyze_density.py`、`check_pixels.py`、`scratch/` 等临时测试碎片自动忽略，确保 Git 历史纯净。

---

## 二、本次所有改动资产全景分类

当前工作区的 156 项待备份改动，高度集中在四大业务域：

```
┌─────────────────────────────────────────────────────────────┐
│ 1. 自媒体自动发布与知识图谱引擎 (本次任务核心)               │
│    - skills/github-knowledge-card (SKILL, 模板库, 设计规范)  │
│    - skills/baoyu-* (文章插画, 知识漫画, 信息图等宝玉技能簇) │
│    - scripts/publish_pipeline.py (小红书防风控清洗发布中间件)│
│    - docs/ (四大详细复盘、升级计划与交付报告)                 │
├─────────────────────────────────────────────────────────────┤
│ 2. Web 演播室与多智能体协同系统 (前期工作)                   │
│    - frontend/src/ (多语言, 监控中心, 演播室, 路由与组件)    │
│    - server/ (API 路由, 权限认证, Alembic 迁移, 数据库模型)  │
│    - config/ (Prometheus, Grafana, Redis, SRS 配置文件)     │
├─────────────────────────────────────────────────────────────┤
│ 3. 手绘短剧与商业变现渲染引擎 (前期工作)                     │
│    - shared_tools/renderers/handdraw/ (手绘短剧渲染引擎)     │
│    - scripts/build_handdraw_* (分镜生成与批量构建脚本)       │
├─────────────────────────────────────────────────────────────┤
│ 4. AOCI 认知资产与基础设施管理                               │
│    - aoci.txt, aoci.code.txt, aoci.meta.txt, .aoci/         │
│    - AGENTS.md, .gitignore, docker-compose.yml              │
└─────────────────────────────────────────────────────────────┘
```

---

## 三、备份实施方案（推荐的分模块原子化 Commit）

为避免一个混乱的庞大 Commit 污染 Git 历史，推荐采用**模块化、语义化原子提交（Atomic Commits）**方案：

### 阶段 1：提交【自媒体自动发布与知识图谱技能引擎】（本次核心产出）
- **包含文件**：
  - `skills/github-knowledge-card/`
  - `skills/baoyu-article-illustrator/`
  - `skills/baoyu-comic/`
  - `skills/baoyu-infographic/`
  - `scripts/publish_pipeline.py`
  - `docs/baoyu_knowledge_graph_cover_integration_guide.md`
  - `docs/workflow_full_pipeline_delivery_report.md`
  - `docs/visual_and_content_optimization_plan.md`
  - `docs/knowledge_graph_visual_engine_upgrade_plan.md`
- **提交信息**：
  `feat(skills): add baoyu suites, github-knowledge-card blueprint engine and publish pipeline`

### 阶段 2：提交【Web 演播室、数字人与全栈基础设施】
- **包含文件**：
  - `frontend/`
  - `server/`
  - `config/`
  - `nginx/`
  - `docker-compose.yml`
  - `tests/`
- **提交信息**：
  `feat(studio): web dance studio, streaming backend and full-stack services`

### 阶段 3：提交【手绘短剧渲染与自动化生产管线】
- **包含文件**：
  - `shared_tools/renderers/handdraw/`
  - `shared_tools/renderers/handdraw_renderer.py`
  - `shared_tools/audio_mastering.py`
  - `scripts/build_handdraw_*.py`
  - `scripts/rebuild_handdraw_pro_video.py`
  - `assets/handdraw/`
- **提交信息**：
  `feat(handdraw): add industrial handdraw renderer and script generation pipelines`

### 阶段 4：提交【AOCI 仓库认知与项目规则】
- **包含文件**：
  - `.gitignore`
  - `.gitattributes`
  - `AGENTS.md`
  - `aoci.txt`
  - `aoci.code.txt`
  - `aoci.meta.txt`
  - `.aoci/`
- **提交信息**：
  `chore(repo): update .gitignore, workspace agents and AOCI cognition index`

---

## 四、远程推送与安全准则（Remote Push Protocol）

根据 `.agents/AGENTS.md` 规则第 6 条：
1. **推送到私有远端 (`origin`)**：
   - 执行：`git push origin feature/web-dance-studio`
   - 用途：完整备份所有代码、配置、自媒体工作流资产。
2. **开源远端 (`opensource`) 隔离保护**：
   - 严禁直接推送到 `opensource/main`；
   - 只有经过脱敏审查（无任何私有域名、账号、特定 API 逻辑）的代码，后续才通过专门的发布分支推送到开源仓库。

---

## 五、一键执行操作指南

您可以随时授权我执行上述四步提交并推送到 GitHub `origin`，或者运行仓库自带的自动化备份脚本：
```bash
# 方式 A：运行一键安全备份脚本
bash scripts/backup_to_github.sh "feat(all): snapshot full-stack studio and automated publishing engine"

# 方式 B：由 Agent 按照原子模块分步提交并推送到 origin
```
