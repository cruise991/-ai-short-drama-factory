# LingCast x AI Short Drama Factory 集成方案

> 版本：v1.0 | 日期：2026-09-11
> 目标：将 LingCast 的数字人直播能力嫁接到现有 AI 短剧工厂，
> 打造「一站式数字人直播带货 + 短视频内容生产」平台。

---

## 一、战略定位：为什么要集成

### 1.1 现状盘点

**我们已有的能力（AI Short Drama Factory）：**

- 端到端短剧/短视频全自动生产管线（策划 → 生产 → QA → 后期 → 分发）
- LivePortrait + Wav2Lip 模型资产（已落地、已调优）
- AI 舞蹈视觉钩子管线（character-dance-video skill，BPM 节拍同步）
- FastAPI + React/Vite Web 工作台（项目管理、Dance Studio）
- MinIO 对象存储 + Docker 容器化部署
- 角色 IP 资产管理（character_bible + motion_library）
- 市场反馈闭环引擎（Growth Loop）

**我们缺失的能力：**

- 实时推流（没有 SRS/WebRTC 网关）
- 数字人直播间交互（弹幕 → LLM → TTS → 口型 → 推流 的实时闭环）
- 直播带货的商品管理 + 话术编排
- 观众端独立应用

**LingCast 提供的能力：**

- 完整的数字人实时直播管线（弹幕 → DeepSeek LLM → Edge-TTS → Wav2Lip → SRS 推流）
- 管理后台 + 观众端双端应用
- 场景视频库 + 闲置推流切换机制
- 知识库 RAG（产品知识检索 → LLM 上下文注入）
- Telegram Mini App 集成
- 字幕叠加 + 抖音风格直播间 UI

### 1.2 集成后的产品形态

    +---------------------------------------------------------+
    |            AI 数字人内容 & 直播一体化平台                  |
    +--------------------------+------------------------------+
    |   内容工厂（现有）        |      直播带货中心（新增）      |
    |                          |                              |
    |  - 短剧自动生产           |  - 数字人形象创建/管理        |
    |  - AI 舞蹈视频            |  - 产品知识库 (RAG)          |
    |  - 全自动 QA 质检         |  - 带货话术编排              |
    |  - 市场反馈闭环           |  - 一键开播（SRS 推流）      |
    |  - IP 资产管理            |  - 实时弹幕互动 (LLM)        |
    |                          |  - 直播间观众端              |
    |                          |  - 直播数据看板              |
    +--------------------------+------------------------------+

---

## 二、技术集成架构

### 2.1 整体架构设计（混合架构）

采用**模块化嫁接**策略：不整体搬迁 LingCast 的 Go 后端，
而是将其核心能力拆解为独立微服务，嫁接到我们的 FastAPI + React 技术栈中。

    统一前端 (React + Vite + TailwindCSS)
    |- 内容工厂看板
    |- Dance Studio
    |- 数字人管理 (新)
    |- 直播控制台 (新)
    |- 商品管理 (新)
    |- 观众端入口 (新)
            |
    FastAPI 网关层 (现有 + 扩展路由)
    |- /api/projects (现有)
    |- /api/dance   (现有)
    |- /api/avatar  (新增)
    |- /api/live    (新增)
    |- /api/product (新增)
    |- /api/chat    (新增)
            |
    +-------+--------+--------+
    |       |        |        |
    v       v        v        v
  AI Worker  TTS微服务  RAG知识库  SRS v5
  (Python)  (FastAPI)  (FastAPI)  (Docker)
  LivePort  Edge-TTS   Jieba     RTMP/FLV
  Wav2Lip   PCM WAV    BM25
  推流编排   S3上传     文档切块

### 2.2 技术栈决策与取舍

| 层面 | 决策 | 理由 |
|------|------|------|
| **后端框架** | 保持 FastAPI（Python），不引入 Go/Gin | 团队技术栈统一，降低维护成本；LingCast 的 Go 层主要做 CRUD 和队列分发，FastAPI 完全胜任 |
| **前端框架** | 保持 React + Vite，吸收 LingCast 的 UI 设计 | 不引入 Next.js 双前端，将观众端做成 React SPA 路由 |
| **AI 推理** | 复用现有 LivePortrait + Wav2Lip，参考 LingCast 的 ONNX 优化 | 模型完全同构，LingCast 的 Wav2Lip ONNX 化值得借鉴 |
| **TTS** | 引入 Edge-TTS 微服务（从 LingCast 移植） | 免费、低延迟、音色丰富，适合直播场景 |
| **推流** | 引入 SRS v5（Docker） | LingCast 已验证方案，HTTP-FLV 分发成熟可靠 |
| **LLM** | 接入 DeepSeek（兼容 OpenAI SDK） | 成本低、中文能力强，带货场景性价比最高 |
| **对象存储** | 复用现有 MinIO | 与 LingCast 的 RustFS 都是 S3 兼容，无缝切换 |
| **消息队列** | 新增 Redis | LingCast 的任务队列 + 直播消息队列依赖 Redis，轻量高效 |
| **数据库** | 保持 SQLite（现有）+ 可选升级 PostgreSQL | 短期 SQLite 足够，用户量上来后平滑迁移 |
| **RAG 知识库** | 移植 LingCast 的 service-rag | 零模型依赖、Jieba 中文全文检索，适合产品知识库场景 |

### 2.3 需要从 LingCast 移植的核心模块

#### 模块 A：TTS 微服务 (service-tts)

- **来源**: LingCast service-tts/
- **功能**: Edge-TTS 合成 → 16kHz/16bit/单声道 PCM WAV → 上传 S3
- **改造**: 适配我们的 MinIO 配置，统一 S3 SDK 调用
- **端口**: :8002

#### 模块 B：RAG 知识库微服务 (service-rag)

- **来源**: LingCast service-rag/
- **功能**: 文档入库切块、Jieba 中文全文检索、BM25 Top-K
- **改造**: 最小改动，直接容器化部署
- **端口**: :8001
- **用途**: 产品说明书 / FAQ / 品牌话术 → 注入 LLM 上下文

#### 模块 C：直播推流 Worker

- **来源**: LingCast worker/ 的实时直播部分
- **功能**: FFmpeg 双管道推流、Wav2Lip 实时口型、闲置视频切换
- **改造**: 整合到我们现有的 AI Worker 进程，共享 LivePortrait/Wav2Lip 模型实例
- **关键技术点**:
  - 常驻 FFmpeg 进程，BGR24 视频 stdin + 音频 /dev/fd/3
  - 口型帧基于当前显示的场景视频切片（不固定一个视频）
  - TTS 预取机制（当前句播放时预合成下一句）

#### 模块 D：SRS 推流网关

- **来源**: LingCast docker-compose 中的 SRS 配置
- **功能**: RTMP 接收 + HTTP-FLV 分发
- **部署**: 直接加入我们的 docker-compose.yml

---

## 三、集成实施路线（四阶段）

### Phase 1：基础设施搭建（预计 1-2 周）

**目标**: 搭建直播所需的基础服务组件

1. **docker-compose.yml 扩展**
   - 新增 SRS v5 服务容器
   - 新增 Redis 7 服务容器
   - 新增 service-tts 容器
   - 新增 service-rag 容器

2. **FastAPI 路由扩展**
   - 新增 server/api/routes/avatar.py — 数字人 CRUD
   - 新增 server/api/routes/live.py — 直播控制（开播/停播/状态）
   - 新增 server/api/routes/chat.py — 弹幕/消息/LLM 回复

3. **数据库 Schema 扩展**
   - avatars 表（形象、音色、人设、base_video_s3_key）
   - scenes / scene_videos 表（场景视频库）
   - live_sessions 表（直播会话）
   - live_messages 表（聊天记录持久化）
   - products 表（商品信息）
   - avatar_knowledge 表（知识库绑定）

**交付物**: docker compose up 能启动全部服务，API 端点可访问

### Phase 2：数字人管理 + 离线口播（预计 2-3 周）

**目标**: 用户可以创建数字人并生成离线带货口播视频

1. **数字人创建工作流**
   - 前端：Avatar Studio 页面（上传形象图 + 选择 Edge-TTS 音色 + 填写人设）
   - 后端：触发 LivePortrait 生成 base 驱动视频（复用现有模型）
   - 存储：base 视频上传 MinIO

2. **离线口播生成**
   - 前端：输入带货脚本 → 提交任务
   - 后端：Edge-TTS 合成 → Wav2Lip 口型同步 → 合成 MP4
   - 播放：xgplayer 9:16 竖屏预览

3. **产品知识库**
   - 前端：知识库管理页面（创建集合、上传文档、绑定数字人）
   - 后端：对接 service-rag 入库/检索

**交付物**: 用户可一键生成数字人口播带货视频，并管理产品知识库

### Phase 3：实时直播上线（预计 3-4 周）

**目标**: 数字人可实时开播，观众可互动

1. **直播推流管线**
   - AI Worker 扩展：常驻 FFmpeg 推流进程管理
   - 闲置视频轮播 + Wav2Lip 实时口型叠加
   - TTS 预取流水线（降低回复延迟）

2. **LLM 互动链路**
   - 弹幕消息 → RAG 知识检索 → DeepSeek LLM 生成回复
   - 回复按句切块 → TTS → Wav2Lip → 推流
   - 带货话术模板注入（system prompt 中预置产品卖点）

3. **直播控制台（管理端）**
   - 一键开播/停播
   - 实时弹幕监控
   - 手动插入话术（紧急产品介绍、促销口播）
   - 直播状态看板

4. **观众端**
   - 直播间列表页（分类筛选）
   - 直播间页面（抖音风格 9:16 竖屏 + 弹幕面板）
   - 游客/注册用户身份体系

**交付物**: 完整的数字人直播带货闭环

### Phase 4：带货增强 + 数据闭环（预计 2-3 周）

**目标**: 让直播带货产生商业价值

1. **商品管理系统**
   - 商品信息 CRUD（名称、价格、卖点、图片、购买链接）
   - 商品与数字人绑定
   - 直播间商品卡片展示 + 点击跳转

2. **智能带货话术引擎**
   - 基于 Growth Loop 引擎（现有）优化话术
   - 分析哪些话术/产品组合转化率高 → 自动调整推荐权重
   - 定时产品轮播（每 N 分钟自动切换主推产品）

3. **直播数据看板**
   - 在线人数、弹幕数、互动率
   - 商品点击/转化追踪
   - 直播回放自动存档（复用 MinIO）

4. **多平台推流**
   - SRS → 抖音/快手/视频号 RTMP 地址
   - 一场直播同时推多个平台

**交付物**: 可商用的数字人直播带货系统

---

## 四、用户使用场景与体验设计

### 4.1 核心设计原则

> **三步开播**：选人 → 选品 → 开播。
> 用户无需理解 LivePortrait、Wav2Lip、SRS 等任何技术概念。

### 4.2 用户旅程

#### 场景一：首次使用 — 创建数字人（约 5 分钟）

    用户操作                           系统后台
    ---------                         ---------
    1. 上传一张人物照片                -> LivePortrait 预处理生成驱动视频
    2. 试听并选择一个声音              -> Edge-TTS 音色列表（缓存加载）
    3. 填写人设（可选）:               -> 写入 avatar 人设字段
       "25岁女性，热情活泼，                注入 LLM system prompt
        擅长美妆推荐"
    4. 点击「创建」                    -> 后台异步处理，约 1-2 分钟
    5. 看到数字人卡片变为「就绪」      -> base 视频生成完毕

#### 场景二：准备带货 — 上传商品和知识（约 10 分钟）

    用户操作                           系统后台
    ---------                         ---------
    1. 进入「商品管理」                -> 商品列表页
    2. 添加商品信息：                  -> 写入 products 表
       名称、价格、卖点、图片
    3. 进入「知识库」                  -> 知识库管理页
    4. 上传产品说明书 / FAQ            -> service-rag 自动切块建索引
    5. 勾选绑定到数字人                -> avatar_knowledge 表关联

#### 场景三：一键开播 — 直播带货（一键操作）

    用户操作                           系统后台
    ---------                         ---------
    1. 进入「直播控制台」              -> 直播管理页面
    2. 选择数字人 + 选择场景           -> 加载场景视频库
    3. 选择今日主推商品                -> 商品信息注入 LLM prompt
    4. 点击「开始直播」                -> 启动 FFmpeg 推流 -> SRS
                                       -> 闲置状态自动口播产品介绍
    5. 观众发弹幕提问                  -> RAG 检索 + LLM 回答
       "这个面霜适合敏感肌吗？"        -> TTS + Wav2Lip -> 实时回复
    6. 点击「插入话术」                -> 手动触发促销口播
       "限时特价，最后 30 份！"
    7. 点击「结束直播」                -> 停止推流，自动存档回放

#### 场景四：复用内容工厂 — 短视频种草（现有能力增强）

    用户操作                           系统后台
    ---------                         ---------
    1. 在「内容工厂」选择带货分支      -> 调用口播管线
    2. 输入产品名 + 卖点               -> LLM 生成带货脚本
    3. 选择数字人                      -> 复用已有 avatar
    4. 一键生成带货短视频              -> TTS + Wav2Lip + 后期合成
    5. 发布到 TikTok / 视频号          -> 市场反馈闭环自动追踪

### 4.3 简化策略总结

| 传统直播带货 | 我们的方案 | 简化效果 |
|-------------|-----------|---------|
| 需要真人主播 + 布景 + 灯光 | 一张照片创建数字人 | 人力成本降至零 |
| 需要编写完整直播脚本 | 上传产品文档自动问答 | 内容准备从小时级到分钟级 |
| 需要推流软件 (OBS) 配置 | 一键开播 | 零技术门槛 |
| 需要客服回答弹幕 | LLM + RAG 自动回复 | 24h 无人值守 |
| 每个平台单独开播 | 多平台同时推流 | 一次操作覆盖全渠道 |
| 直播结束数据散落 | 自动数据看板 + 回放存档 | 复盘效率大幅提升 |

---

## 五、Docker Compose 扩展方案

在现有 docker-compose.yml 基础上新增以下服务：

    # === 新增：直播带货基础设施 ===

    redis:
      image: redis:8.2.2-alpine
      container_name: drama_redis
      ports:
        - "6379:6379"
      volumes:
        - redis_data:/data
      restart: unless-stopped

    srs:
      image: ossrs/srs:5
      container_name: drama_srs
      ports:
        - "1935:1935"   # RTMP 推流
        - "8080:8080"   # HTTP-FLV 拉流 + API
      volumes:
        - ./config/srs.conf:/usr/local/srs/conf/srs.conf
      restart: unless-stopped

    service-tts:
      build:
        context: ./services/tts
      container_name: drama_tts
      ports:
        - "8002:8002"
      environment:
        - S3_ENDPOINT=http://minio:9000
      depends_on:
        - minio
      restart: unless-stopped

    service-rag:
      build:
        context: ./services/rag
      container_name: drama_rag
      ports:
        - "8001:8001"
      volumes:
        - rag_data:/app/zvec_data
      restart: unless-stopped

---

## 六、前端路由规划

    /                       -> 仪表盘（项目概览 + 直播状态）
    /projects               -> 内容工厂项目列表（现有）
    /projects/:id           -> 项目详情（现有）
    /dance-studio           -> AI 舞蹈工作室（现有）
    /avatars                -> 数字人列表（新增）
    /avatars/create         -> 数字人创建（新增）
    /avatars/:id            -> 数字人详情 / 编辑（新增）
    /avatars/:id/scenes     -> 场景视频管理（新增）
    /products               -> 商品管理（新增）
    /knowledge              -> 知识库管理（新增）
    /live                   -> 直播控制台（新增）
    /live/:id               -> 直播间管理（新增）
    /live/:id/viewer        -> 观众端直播间（新增）
    /analytics              -> 数据看板（新增）

---

## 七、风险评估与应对

### 7.1 技术风险

| 风险 | 等级 | 应对策略 |
|------|------|---------|
| Wav2Lip 实时推理延迟过高 | 高 | 采用 LingCast 的 ONNX 优化方案；考虑 TensorRT 加速；设置 TTS 预取缓冲 |
| 单 GPU 并发直播数受限 | 中 | Phase 1 设计为单机单播；后期支持多 Worker 水平扩展 |
| SRS 推流稳定性 | 低 | SRS v5 成熟方案，加 watchdog 心跳监测；掉线自动重连 |
| Edge-TTS 依赖微软云服务 | 中 | 本地 TTS 备选（如 Kokoro）；TTS 结果缓存复用 |
| LLM 回复延迟影响直播体验 | 中 | DeepSeek streaming 流式输出；按句切块不等整段回复；预测性闲聊填充 |

### 7.2 产品风险

| 风险 | 等级 | 应对策略 |
|------|------|---------|
| 数字人形象不够真实 | 中 | 支持多场景视频库（不同角度/动作）；闲置切换增加真实感 |
| 带货话术机械重复 | 中 | Growth Loop 引擎持续优化；支持多话术模板随机组合 |
| 平台合规（虚拟人标识） | 高 | 直播间增加 AI 数字人 标识；遵守各平台规则 |

---

## 八、里程碑与预期产出

| 阶段 | 周期 | 交付里程碑 | 用户可做的事 |
|------|------|-----------|-------------|
| Phase 1 | 第 1-2 周 | 基础设施就绪，API 可访问 | (内部验证) |
| Phase 2 | 第 3-5 周 | 数字人管理 + 离线口播 | 上传照片创建数字人，生成带货短视频 |
| Phase 3 | 第 6-9 周 | 实时直播上线 | 一键开播，观众弹幕互动，LLM 自动回复 |
| Phase 4 | 第 10-12 周 | 带货增强 + 数据闭环 | 商品管理，智能话术，多平台推流，数据看板 |

**最终预期**：用户从「有一张人物照片」到「数字人在抖音直播间带货回答观众问题」，
全程操作不超过 15 分钟，技术门槛为零。
