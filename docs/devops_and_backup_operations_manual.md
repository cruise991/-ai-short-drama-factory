# AI 短剧工厂 — 系统运维与安全备份操作手册 (DevOps & Backup Manual)

> **文档版本**：v2.0.0  
> **更新时间**：2026-09-08  
> **适用对象**：系统运维工程师、全栈开发者、DevOps、技术负责人  
> **适用环境**：本地 macOS / Linux 工作站、Docker 生产容器集群、GitHub 双远程仓库  

---

## 一、 系统架构与运维拓扑蓝图 (Architecture & Topology)

### 1. 服务与端口拓扑矩阵

系统支持**「本地极速热重载开发」**与**「Docker 生产隔离容器」**双轨运行：

| 服务组件 | 运行模式 | 监听端口 | 访问路径 / 协议 | 职责与反向代理目标 |
| :--- | :--- | :--- | :--- | :--- |
| **Frontend (Dev)** | 本地 Vite 开发服务 | `5173` | `http://localhost:5173/` | 前端 React 页面实时热更新调试，代理 `/api`、`/media`、`/ws` 至后端 |
| **Frontend (Prod)** | Docker 容器 (Nginx) | `3008` | `http://localhost:3008/` | 生产静态 Web 看板，内置 Nginx 高性能反向代理 |
| **Backend API** | FastAPI (uvicorn) | `8008` (Docker 映射)<br>`8000` (容器内) | `http://localhost:8008/` | 核心业务 API、项目管理、舞蹈任务调度、WebSocket 实时日志推送 |
| **Media Server** | 静态媒体挂载 | 映射于 `8008` 与 `3008` | `http://localhost:3008/media/*` | 成品视频、分镜切片、参考立绘、封面海报直接访问服务 |
| **Worker Engine** | Python 异步子进程 | 宿主机/容器内运行 | 内存队列 / SQLite | 执行生图、视频渲染、FFmpeg 锐化混音与 20s 闭环质检流水线 |

```mermaid
graph LR
    User["用户浏览器 / Ego Lite"] -->|3008 生产端口| Nginx["Frontend 容器 (Nginx:alpine)<br>Port: 3008"]
    User -->|5173 开发端口| Vite["Vite Dev Server<br>Port: 5173"]

    Nginx -->|/ (静态 Bundle)| StaticFiles["dist/ 静态页面"]
    Nginx -->|/api/* 代理| FastAPI["Backend (FastAPI)<br>Port: 8000 / 8008"]
    Nginx -->|/media/* 流媒体代理| FastAPI
    Nginx -->|/ws/* WebSocket 代理| FastAPI

    Vite -->|/api, /media, /ws| FastAPI
    FastAPI --> SQLite[("SQLite 数据库<br>server/data/app.db")]
    FastAPI --> Worker["视频生成与后处理管道 (Worker)"]
    Worker --> Agnes["Agnes Cloud API<br>(Vision 2.5 / Image / Video)"]
    Worker --> R2["Cloudflare R2 对象存储"]

    style Nginx fill:#4ecdc4,color:#fff
    style FastAPI fill:#45b7d1,color:#fff
    style R2 fill:#f9ca24,color:#333
```

---

### 2. Nginx 生产反向代理关键配置规范

位于 [`frontend/nginx.conf`](file:///Users/workspace/ai_short_company/ai-short-drama/frontend/nginx.conf)，必须满足以下生产特性：
1. **大文件直传支持**：`client_max_body_size 100M;`（防止用户上传 4K/超清参考图时发生 HTTP 413 Payload Too Large）；
2. **超长管道连接保活**：`proxy_read_timeout 600s;`、`proxy_send_timeout 600s;`（保证 30s 复杂视频生成期间连接不中断）；
3. **WebSocket 握手升级**：
   ```nginx
   location /ws/ {
       proxy_pass http://backend:8000/ws/;
       proxy_http_version 1.1;
       proxy_set_header Upgrade $http_upgrade;
       proxy_set_header Connection "upgrade";
   }
   ```
4. **单页应用客户端路由 Fallback**：`try_files $uri $uri/ /index.html;`。

---

## 二、 GitHub 双轨制安全备份规范 (GitOps Backup Strategy)

根据项目核心规范，系统严格采用**双远程仓库隔离机制**，坚决杜绝代码泄露与历史污染：

```text
远程仓库划分：
├── origin     -> https://github.com/cruise991/ai-short-drama.git          (私有主开发库 - 全量安全备份)
└── opensource -> https://github.com/cruise991/-ai-short-drama-factory.git (公开开源库 - 严苛脱敏发布)
```

### 1. 本地 Pre-Push 防误推与敏感扫描门禁

为了防止因开发者手滑误敲 `git push opensource` 将私有敏感代码推到公网，我们在 [`.git/hooks/pre-push`](file:///Users/workspace/ai_short_company/ai-short-drama/.git/hooks/pre-push) 配置了双重安全门禁：

1. **开源仓库硬性拦截**：
   - 默认禁止一切向 `opensource` 远程的推送；
   - 只有显式注入授权环境变量 `ALLOW_OPENSOURCE_PUSH=1` 时方可放行。
2. **敏感特征正则扫描**：
   - 自动扫描拟推送的 Commit Diff 中是否包含疑似密钥（如 `sk-[a-zA-Z0-9]{32,}`、`AIza...`、`ghp_...` 等）；
   - 一旦发现高危明文，推送将在网络建立前被本地紧急熔断。

---

### 2. 自动化一键备份工具 (`backup_to_github.sh`)

位于 [`scripts/backup_to_github.sh`](file:///Users/workspace/ai_short_company/ai-short-drama/scripts/backup_to_github.sh)，为团队日常开发提供秒级一键安全备份能力。

#### 核心执行流程：
1. **敏感文件扫描**：扫描未被 `.gitignore` 保护的 `.env`、`*.key`、`*.db`；
2. **大文件体积预检**：拦截未忽略的 >50MB 二进制文件；
3. **远程对齐校验**：对比本地 HEAD 与 `origin` 远端状态；
4. **自动暂存、规范提交与安全推送到私有库**。

#### 常用操作指令：
```bash
# 模式 A：纯检查状态（不执行 commit，不 push）
./scripts/backup_to_github.sh --status-only

# 模式 B：一键备份（自动扫描、暂存并推送到当前分支的 origin）
./scripts/backup_to_github.sh "feat(dance): 完成新特性验证并提交"
```

---

## 三、 数据持久化与工作区资产快照 (Data & State Backup)

### 1. SQLite 数据库热备份机制

SQLite 文件（`server/data/app.db`）记录了所有任务状态、项目元数据与历史生成日志，由于已加入 `.gitignore`，必须通过独立工具进行定期快照。

- **快照工具脚本**：[`scripts/backup_system_snapshot.py`](file:///Users/workspace/ai_short_company/ai-short-drama/scripts/backup_system_snapshot.py)
- **核心操作**：
  1. **无锁安全热备份**：调用 SQLite 原生 `src_conn.backup(dst_conn)`，在服务持续运行无锁状态下生成带时间戳快照：`archive/backups/app_YYYYMMDD_HHMMSS.db`；
  2. **人类可读数据导出**：自动将数据库表数据导出为结构化 JSON：`archive/backups/db_export_latest.json`，用于跨平台对账或灾备迁移；
  3. **父级规则镜像归档**：自动将父目录 `/Users/workspace/ai_short_company/.agents/AGENTS.md` 镜像复制至 [`docs/rules/WORKSPACE_AGENTS.md`](file:///Users/workspace/ai_short_company/ai-short-drama/docs/rules/WORKSPACE_AGENTS.md)，确保团队全局规则纳入版本库。

#### 执行快照备份：
```bash
python3 scripts/backup_system_snapshot.py
```

---

### 2. 环境配置字典规约模板

为防止灾难恢复时因丢失环境变量导致无法启动，仓库已建立标准化模板：
- **全局根配置模板**：[`.env.example`](file:///Users/workspace/ai_short_company/ai-short-drama/.env.example)（包含 Agnes 密钥池、Cloudflare R2 存储凭据、MinIO 配置、服务端口）
- **前端配置模板**：[`frontend/.env.example`](file:///Users/workspace/ai_short_company/ai-short-drama/frontend/.env.example)（包含后端服务端口与 API 地址）

> **安全准则**：严禁在 `.env.example` 中填写真实密码或密钥；真实 `.env` 必须妥善保存在离线企业密码管理器中。

---

## 四、 Docker 生产环境运维指南 (Docker Operations)

### 1. 常用集群管理指令

```bash
# 1. 检查所有服务容器运行状态
docker compose ps

# 2. 查看前端 Nginx 访问与反代实时日志
docker compose logs -f frontend

# 3. 查看后端 API 与 Worker 执行日志
docker compose logs -f backend

# 4. 进入后端容器内部调试
docker compose exec backend bash

# 5. 进入前端容器内部检查 Nginx 配置
docker compose exec frontend sh
```

### 2. 前端零下线秒级重新编译与部署

当修改前端 React 代码（如 `DanceStudio.tsx`、多语言词条）后，采用本地轻量预构建 + 容器秒级热重载：

```bash
# 步骤 1：本地极速构建静态产物
cd frontend && npm run build && cd ..

# 步骤 2：秒级重构前端镜像（使用本地缓存 nginx:alpine，无海外拉取延迟）
docker compose build frontend

# 步骤 3：无缝更新前端容器
docker compose up -d --no-deps frontend
```

---

## 五、 存储空间与多模态资产治理 (Storage Governance)

| 资产分类 | 典型目录 | 体积规模 | 存储介质 | 生命周期与清理规则 |
| :--- | :--- | :--- | :--- | :--- |
| **核心源码与前端** | `frontend/`, `server/` | ~30 MB | **GitHub 私有库** | 随 Git 历史永久增量保留。 |
| **动作模版规则** | `assets/dance/07_templates/` | < 2 MB | **GitHub 私有库** | JSON 格式，随代码版本管理。 |
| **AI 模型权重** | `models/` | ~2.19 GB | **外部模型源 / 对象存储** | 严禁进 Git；通过 `download_skills.py` 自动化按需拉取。 |
| **中间视频切片与临时帧** | `projects/*/runs/`, `tmp_*/` | ~2-10 GB | **本地磁盘暂存** | 任务完成后由清理脚本安全回收。 |
| **最终成片成果** | `out/` | ~714 MB | **Cloudflare R2** | 任务完成后自动直传 R2，本地保留 14 天后清理。 |

#### 自动化磁盘瘦身工具：
```bash
# 安全清理过期临时目录、系统缓存与冗余切片（保留最终成片与关键基线）
python3 scripts/clean_workspace.py
```

---

## 六、 极端灾难恢复 SOP (Disaster Recovery Runbook)

### 场景一：全新机器或系统损坏后极速恢复（目标 RTO < 5 分钟）

1. **从私有仓库克隆代码**：
   ```bash
   git clone -b feature/web-dance-studio https://github.com/cruise991/ai-short-drama.git
   cd ai-short-drama
   ```
2. **还原环境凭证文件**：
   ```bash
   cp .env.example .env
   cp frontend/.env.example frontend/.env
   # 从密码管理器中复制填入实际 AGNES_API_KEY 与 R2 密钥
   ```
3. **安装本地 Git 安全钩子**：
   ```bash
   chmod +x scripts/hooks/pre-push
   cp scripts/hooks/pre-push .git/hooks/pre-push
   ```
4. **一键构建并拉起 Docker 生产集群**：
   ```bash
   docker compose up -d --build
   ```
5. **验证服务健康度**：
   - 打开浏览器访问：`http://localhost:3008/dance`
   - 检查 API 健康度：`curl -I http://localhost:8008/health`

---

### 场景二：数据库异常回滚或数据迁移

1. **查找最近的历史快照**：
   ```bash
   ls -lt archive/backups/app_*.db | head -n 5
   ```
2. **恢复数据库文件**：
   ```bash
   # 停止后端容器避免锁冲突
   docker compose stop backend
   
   # 还原目标快照
   cp archive/backups/app_20260907_144246.db server/data/app.db
   
   # 重启后端服务
   docker compose start backend
   ```

---

### 场景三：开源脱敏发布合规操作 SOP

当业务功能在私有库经过完整验证，计划对外发布开源版本时：
```bash
# 步骤 1：本地执行严格的安全密钥检查
grep -rnE "(sk-[a-zA-Z0-9]{32,}|AIza)" . --exclude-dir={.git,node_modules,archive}

# 步骤 2：切换或准备脱敏发布分支
git checkout main

# 步骤 3：使用授权环境变量触发安全推送至开源库
ALLOW_OPENSOURCE_PUSH=1 git push opensource main
```
