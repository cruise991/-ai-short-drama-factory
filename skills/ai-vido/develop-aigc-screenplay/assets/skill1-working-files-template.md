# Skill 1 工作文件模板

本模板只在项目文件模式使用，不要求用户填写，也不要求一次创建全部文件。方向成立前最多维护以下四份探索文件；正式大纲和交接合同只在完整故事成熟后生成。

## 探索期文件

### `creative-north-star.md`

```markdown
# 创作北极星

## 项目边界
- 作品形态：
- 目标时长／集数：
- 平台／放映场景：
- 媒介与制作路径：

## 观众承诺
- 点进来的理由：
- 持续观看的主要问题：
- 核心情绪释放：
- 最终余味：

## 戏剧与主题
- 结构剖面：任务驱动／关系驱动／观察累积／诗性实验／混合
- 当前价值问题：
- 主要人物／关系：
- 类型或形式承诺：

## 创作重力
- 必须保留：
- 明确拒绝：
- 强偏好：
- 可自由探索：
- 暂定推断：

## 创作记忆
- 已确认：
- 用户明确否决及根因：
- 已验证失败的默认方向：
- 最近输入的层级与最低必要影响范围：
```

### `story-engine.md`

```markdown
# 故事发动机

## 默认电影与反惯性
- 素材最容易生成的默认电影：
- 必须保留的类型承诺：
- 必须重造的惯性方法：

## 当前母体发动机
- 特定主角、当前欲望与惯用策略：
- 失衡事件以及为什么必须现在行动：
- 主要压力来源；若有战略对手，其目标与获胜方式：
- 对手或压力怎样读取并反制主角：
- 局部成功怎样制造更大后果：
- 中段什么发生不可逆变化：
- 旧策略怎样失败或被重新评价：
- 终局中什么不能兼得：
- 人物作出什么决定并怎样成为物理行动：
- 结果、代价、关系状态和唯一开放问题：

## 因果传播
特定主角与旧策略 → 失衡事件 → 初始行动 → 对手读取与反制 → 升级后果 → 中段不可逆变化 → 旧策略失败 → 终局选择 → 物理结果与余波

## 人物、关系与压力
- 主角的决策系统：
- 核心关系的相互需要、不兼容与权力变化（若适用）：
- 战略对手的信息、适应、约束与盲点，或非战略压力的累积规则：

## 内部淘汰与保护
- 淘汰的根因：
- 吸收的叶层优点：
- 当前脆弱项：
- 必须保护：
```

### `research-notes.md`（可选）

只在事实准确性、特定文化语境或专业机制会改变故事因果时创建。区分来源事实、创作推断和审美判断；不把资料堆积成世界观百科。

```markdown
# 研究笔记

| 问题 | 来源事实 | 创作推断 | 对故事的最低必要影响 |
|---|---|---|---|
|  |  |  |  |
```

### `story-proof.md`

```markdown
# 电影故事证明

## 暂定片名与观影承诺

## 完整故事
从第一个可见／可听事件连续写到最后一个画面。按有意义的故事段落组织，不显示内部候选树或功能表。

## 情绪路径

## 三至五个重要电影场面及其因果作用

## 三项电影压力证明
- 开场合同：
- 连续压力场：
- 高潮因果图：

## 四项硬测试结论
- 占位符测试：
- 对手自主测试：
- 高潮归因测试：
- 主题—机制测试：

## 结尾边界
- 本片明确解决：
- 即时代价：
- 核心关系当前状态：
- 唯一开放问题：

## 自检
- 阻断：
- 脆弱：
- 成立：
- 必须保护：
- 定性魅力判断：
```

## 成熟后文件

### `outline-v1.0.md`

用户批准当前完整故事后，把 `story-proof.md` 中面向创作执行的完整故事快照为正式大纲。保留故事正文、情绪路径和重要场面，并附：

```markdown
## 锁定范围
- 结构剖面：
- 观众承诺：
- 主角／视点／目标：
- 战略对手目标与主要策略（若适用）：
- 核心任务，或观看任务与累积规则：
- 关系依赖与冲突（若适用）：
- 主要不可逆转折：
- 高潮或终局机制：
- 结尾结果与主余味：

## 剧本阶段自由范围
- 

## 批准记录
- 用户原话：
- 批准时间：
- 获准进入：`draft-aigc-screenplay`
```

### `skill1-handoff.json`

正式批准时使用 `review_status: approved`、`handoff_mode: formal` 并指向 `outline-v1.0.md`。只有用户明确要求一次性跑完整工作流时，才可在未批准状态使用 `pending_review / provisional` 并指向 `story-proof.md`；不得伪造批准。与当前结构无关的字段使用 `null`，不得为了填满合同改写故事。

```json
{
  "schema_version": "1.1",
  "review_status": "approved",
  "handoff_mode": "formal",
  "structure_profile": "",
  "outline_file": "outline-v1.0.md",
  "outline_version": "v1.0",
  "format": {
    "form": "",
    "target_duration": "",
    "platform": "",
    "medium": ""
  },
  "audience_promise": [],
  "protagonists": [],
  "point_of_view": "",
  "opponent": null,
  "pressure_source": "",
  "core_relationship": null,
  "mission": null,
  "viewing_task": "",
  "accumulation_rule": "",
  "major_sequences": [],
  "terminal_resolution": {
    "mode": "traditional_climax_or_nontraditional_culmination",
    "choice": "",
    "physical_resolution": "",
    "irreversible_final_state": "",
    "established_dependencies": []
  },
  "ending": {
    "resolved": [],
    "immediate_cost": [],
    "single_open_question": ""
  },
  "causal_world_rules": [],
  "locked_elements": [],
  "flexible_elements": [],
  "major_production_risks": [],
  "routing": {
    "next_skill": "draft-aigc-screenplay",
    "may_continue_provisionally": false
  },
  "approval": {
    "user_words": "",
    "approved_at": "",
    "authorized_next_stage": "draft-aigc-screenplay"
  }
}
```
