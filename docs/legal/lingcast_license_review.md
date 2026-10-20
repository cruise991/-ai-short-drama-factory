# LingCast 许可证与开源合规审查报告 (LingCast License Review)

## 一、审查背景与目标
为确保将 LingCast（高质量低延迟数字人驱动框架）深度融合进本平台的合法性与商用安全性，规避开源许可传染（GPL 风险）及非商业限制（CC-BY-NC 风险），法务与架构部门联合开展本专项审查。

---

## 二、LingCast 许可证与资产构成核查

| 资产组成部分 | 来源 / 载体 | 常见开源许可证 | 商用风险评级 | 合规准入条件 |
| :--- | :--- | :--- | :--- | :--- |
| **推理管道源码** | GitHub 仓库 | Apache 2.0 / MIT | **低风险** | 保留原作者版权声明及 License 文本 |
| **预训练基座权重** | HuggingFace / ModelScope | CC-BY-NC 4.0 或 Apache 2.0 | **中/高风险**（需以发布页实际标注为准） | 若含 Non-Commercial 限制，生产收费服务须联系原作者签署商业特许协议 |
| **人脸特征提取器** | InsightFace / Dlib 模块 | InsightFace 非商用许可 | **极高风险** | **严禁在生产商用镜像打包 InsightFace 默认预训练模型**；须替换为合规开源特征库 (如 OpenFace/FaceAlignment MIT 许可) |
| **声学驱动器** | Wav2Vec2 / Hubert | Apache 2.0 / MIT | **低风险** | 允许合法免费商用 |

---

## 三、生产环境风险防范与架构隔离策略

### 1. 微服务进程隔离（Process & Container Isolation）
- LingCast 仅作为独立的 Worker 容器（`live_worker`）运行，通过标准网络协议（Redis Streams / HTTP gRPC）与主业务系统解耦。
- **杜绝代码侵入传染**：严禁在主业务后端（FastAPI）或前端代码中静态编译或直接 `import` 具有潜在传染性许可的第三方模块。

### 2. 双轨驱动机制（Dual-Track Driver Architecture）
- **开源/免费演练轨**：配置轻量级、完全免费可商用的基座方案（如 LivePortrait / Open Avatar Driver）；
- **生产商用授权轨**：在具备商业授权凭证的前提下，挂载 LingCast 商业优化权重，确保任何商业变现流无版权瑕疵。

---

## 四、审查结论与准入批示
1. **原则同意引入**：同意在 Phase 1 和 Phase 2 中将 LingCast 部署为独立的底层推理引擎服务容器；
2. **强制前置条件**：生产上线前，DevOps 与法务须在构建镜像阶段核验所下载的 Checkpoint 模型权重具体 License，并将审查记录归档至 `docs/legal/`。
