# Release Notes

## v3.0.0

中文分支 v3 维护升级。

### 重点更新

- 新增 `skills/last30days` 自包含 Agent Skills 运行载荷。
- 中文 CLI 统一使用单入口 `last30days.py`，根目录和 Skill 载荷保持同名结构。
- 新增 `--emit html` 和 `--emit html-path`，支持生成可离线打开的 `report.html`。
- 引入受 `op7418/guizang-ppt-skill` 启发的 Swiss/IKB HTML 报告样式。
- README、Skill 说明、SPEC 与同步脚本统一改为推荐 `last30days.py`。
- README 在原先长文档基础上合入 v3 内容，保留免责声明、平台支持、配置、评分系统和中英文说明。

### 修复与改进

- 小红书和知乎在 API 与 Playwright 路径返回空结果时，增加公开站内搜索兜底。
- `quick` 模式下小红书和知乎跳过较慢的 Playwright 路径，避免长时间等待后超时。
- 小红书和知乎空结果时会明确说明已尝试路径和可能原因。
- `--diagnose` 在可尝试兜底路径时会把小红书标记为可用。
- 增加小红书/知乎兜底解析与可用性诊断回归测试。
- 增加 HTML 渲染回归测试。

### 兼容性

根目录 `scripts/` 仍保留用于本地开发和旧用法。通过 Agent Skills 安装时，推荐使用 `{{SKILL_DIR}}/scripts/last30days.py`。

### 已知限制

小红书和知乎仍可能因登录态失效、验证码/反爬、平台 API 变化、搜索引擎未收录公开链接而返回 0 条。当前版本会明确暴露原因，不再静默失败。

### 验证

```bash
py -m pytest tests/test_html_render.py tests/test_render_wechat.py
```

## v2.1.0

- 修复微信公众号渲染回归。
- 改进百度与小红书兜底行为。
- 增加爬虫和反爬相关回归覆盖。

## v2.0.0

- 增加受 MediaCrawler 启发的 Playwright 兜底路径。
- 降低强制 API Key 依赖。
- 增加多 Agent 兼容文档。

## v1.0.0

- 首次完成 `mvanhorn/last30days-skill` 的中文平台本土化。

