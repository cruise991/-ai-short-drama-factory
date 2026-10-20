# LingCast 智能直播系统 · 生产环境部署与运维指南 (v2.0)

> **版本**：v2.0 生产交付版  
> **更新时间**：2026年9月  
> **适用环境**：Linux (Ubuntu 22.04 LTS / Debian 12 / RHEL 9), Docker 24.0+, Docker Compose v2.20+

---

## 1. 生产环境硬件与网络推荐规范

| 组件类型 | 最低配置 (开发/测试) | 生产推荐配置 (单实例中型集群) | 超大型高并发集群 (10+ 并发直播间) |
| :--- | :--- | :--- | :--- |
| **应用计算 (CPU)** | 4 核 x86_64 / ARM64 | 8 核 16 线程 | 32 核 64 线程分布式实例 |
| **内存 (RAM)** | 8 GB | 16 GB ~ 32 GB | 64 GB+ 高频 ECC 内存 |
| **GPU 推理加速** | 无 (纯 CPU 仿真) | NVIDIA T4 / RTX 4090 (16GB 显存) | NVIDIA A10G / A100 (40GB/80GB) |
| **磁盘空间 (NVMe)** | 50 GB SSD | 200 GB NVMe (RAID 10) | 1 TB+ 分布式挂载存储 (NAS/Ceph) |
| **上行网络带宽** | 10 Mbps | 50 Mbps 独享带宽 | 200 Mbps+ BGP 优质公网专线 |

---

## 2. 生产架构拓扑与服务端口规划

```
                 [ 观众浏览器 / 客户端 ]       [ 运营管理中台 ]
                            │                        │
               HTTP/HTTPS (80/443)              HTTP/HTTPS (80/443)
                            ▼                        ▼
                   ┌──────────────────────────────────┐
                   │        Nginx 统一接入网关         │
                   │    (SSL 终结 / 反向代理 / 负载均衡) │
                   └──────────┬───────────┬───────────┘
                              │           │
            WebSocket / REST  │           │ HTTP-FLV 拉流 (8085)
                              ▼           ▼
        ┌─────────────────────────┐   ┌─────────────────────────┐
        │   FastAPI 业务核心集群   │   │     SRS 6.0 媒体服务器   │
        │   (short_drama_api)     │   │   (short_drama_srs)     │
        │   8000 (反代隐藏)        │   │   1935 (RTMP) / 8085    │
        └─────────────┬───────────┘   └───────────▲─────────────┘
                      │                           │
                      │ 异步事件总线               │ FFmpeg 实时推流
                      ▼                           │
        ┌─────────────────────────┐               │
        │     Redis 7.0 集群      │───────────────┘
        │   (short_drama_redis)   │
        │   Pub/Sub / Stream / 缓存│
        └─────────────┬───────────┘
                      │ 持久化读写
                      ▼
        ┌─────────────────────────┐
        │   PostgreSQL 16 关系库  │
        │  (short_drama_postgres) │
        │  5432 (仅内网容器互联)   │
        └─────────────────────────┘
```

### 端口映射矩阵

| 服务名称 | 容器内部端口 | 主机外部暴露 | 访问协议 | 安全与网络隔离策略 |
| :--- | :--- | :--- | :--- | :--- |
| **Nginx 网关** | 80, 443 | `80`, `443` | HTTP, HTTPS | 公网直接可达，配置 WAF 防火墙与 Let's Encrypt 证书 |
| **SRS 媒体服务器** | 1935, 8085 | `1935`, `8085` | RTMP, HTTP-FLV | RTMP (推流) 限内网或密钥授权；8085 (拉流) 经 Nginx 缓存反代 |
| **FastAPI 核心服务** | 8000 | 内网桥接 | HTTP, WebSocket | 禁止公网直接映射，仅由 Nginx 经 `upstream backend` 代理 |
| **PostgreSQL 16** | 5432 | 内网桥接 | TCP / PostgreSQL | 严禁暴露公网，仅允许 `shortdrama_network` 内部容器连接 |
| **Redis 7.0** | 6379 | 内网桥接 | TCP / Redis RESP | 设置强密码鉴权，严禁外部公网直接访问 |

---

## 3. 环境变量与安全机密配置

生产环境严禁使用默认弱密码。请在 `server/.env` 或服务器主机环境变量中注入以下密钥：

```bash
# ==============================================================================
# 数据库与缓存安全凭证
# ==============================================================================
POSTGRES_DB=shortdrama_db
POSTGRES_USER=shortdrama_prod
POSTGRES_PASSWORD=P@ssw0rd_LingCast_Prod_2026_SecureKey!
DATABASE_URL=postgresql://shortdrama_prod:P@ssw0rd_LingCast_Prod_2026_SecureKey!@postgres:5432/shortdrama_db

REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=R3dis_LingCast_Prod_StrongAuth_2026!
REDIS_URL=redis://:R3dis_LingCast_Prod_StrongAuth_2026!@redis:6379/0

# ==============================================================================
# JWT 鉴权与安全令牌
# ==============================================================================
JWT_SECRET_KEY=9f8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0a9b8c7d6e5f4a3b2c1d0e
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

# ==============================================================================
# AI 大模型与语音合成服务配置 (必须严格遵循接口规范)
# ==============================================================================
AGNES_API_KEY=sk-prod-your-real-agnes-token-here
AGNES_BASE_URL=https://apihub.agnes-ai.com/v1
DEFAULT_LLM_MODEL=agnes-3.0-flash
FALLBACK_LLM_MODEL=agnes-2.5-flash

# ==============================================================================
# 法律合规与数字人水印标识
# ==============================================================================
REQUIRE_WATERMARK=true
STATUTORY_AI_WATERMARK_TEXT="AI虚拟数字人直播中 · 请理性消费 (网信办备案: 310104-2026-0089)"
```

---

## 4. 标准化上线发布流程

生产发布由自动化运维脚本驱动，支持平滑构建、数据库迁移与健康校验。

### 4.1 首次部署与常规发布

```bash
# 1. 克隆生产代码库或拉取最新稳定 release tag
cd /workspace/ai_short_company/ai-short-drama

# 2. 执行一键发布流水线 (含构建、迁移、健康巡检)
bash scripts/deploy_prod.sh
```

### 4.2 运维巡检与服务存活监测

部署完成后，系统提供一键式全栈健康度巡检脚本：

```bash
bash scripts/healthcheck.sh
```

**巡检输出指标**：
- Docker 容器健康运行状态 (`docker ps`)
- 数据库连接与表结构完整性检查
- Redis 消息总线 PING/PONG 响应
- FastAPI 核心健康端点 `/healthz` 响应码与延迟
- 敏感词过滤系统 (DFA) 自检

---

## 5. 容灾备份与恢复手册

系统采用“**每日定时全量冷备 + 校验和防篡改核验 + 7天滚动清理**”的容灾策略。

### 5.1 执行自动化快照备份

```bash
# 手动触发或配置为 Linux crontab 任务 (每日凌晨 02:00)
# 0 2 * * * /workspace/ai_short_company/ai-short-drama/scripts/backup_postgres.sh >> /var/log/pg_backup.log 2>&1
bash scripts/backup_postgres.sh
```
- 备份目录：`data/backups/postgres/`
- 产出文件：`pg_backup_YYYYMMDD_HHMMSS.sql.gz` 及其 SHA-256 校验和文件 `.sha256`。

### 5.2 灾难应急恢复流程

若遇数据误删或硬件故障，运维人员可使用自动化核验恢复工具：

```bash
# 校验 SHA-256 完整性并恢复数据库
bash scripts/restore_postgres.sh data/backups/postgres/pg_backup_20260911_120000.sql.gz
```
> **安全防护机制**：若备份文件被篡改或哈希不匹配，脚本将自动拦截并拒绝执行还原，保障数据安全性。

---

## 6. 监控告警与可观测性集成

- **Prometheus 指标抓取端点**：`http://<服务器内网IP>:8000/metrics`
  - 直播在线观众数：`lingcast_active_viewers`
  - 弹幕吞吐 QPS：`lingcast_danmaku_inflow_total`
  - 敏感词拦截量：`lingcast_compliance_violations_total`
  - TTS 合成延迟：`lingcast_tts_synthesis_duration_seconds`
- **结构化 JSON 日志归集**：
  - 日志格式已全面结构化，内置敏感凭证（Token、API Key、DB 密码）自动脱敏掩码过滤；
  - 推荐使用 Fluentd / Logstash 收集容器 stdout 并接入 ElasticSearch / Grafana Loki。

---

## 7. 常见故障应急排查与恢复预案

| 故障现象 | 可能根因 | 应急处置步骤 |
| :--- | :--- | :--- |
| **拉流画面卡顿或黑屏** | SRS 服务异常或推流端口断开 | 1. 检查 `docker logs short_drama_srs`<br>2. 确认 1935/8085 端口监听状态<br>3. 重启媒体容器：`docker compose restart srs` |
| **弹幕无回复 / 互动停滞** | LLM 接口超时或配额超限 | 1. 检查 `short_drama_api` 日志排查 API Key 状态<br>2. 系统自动降级到 `agnes-2.0-flash` 备用模型<br>3. 重启编排器进程 |
| **观众投诉存在违规广告词** | 话术库或弹幕出现新型绕过词 | 1. 进入运营中台【知识库与话术中心】<br>2. 添加违禁词至 DFA 词表，立即生效无需重启服务 |
| **数据库磁盘利用率 > 85%** | 历史备份文件堆积 | 1. 检查 `data/backups/postgres/`<br>2. 调整 `scripts/backup_postgres.sh` 中 `RETENTION_DAYS=3`<br>3. 执行转储至冷存储 OSS/S3 |
