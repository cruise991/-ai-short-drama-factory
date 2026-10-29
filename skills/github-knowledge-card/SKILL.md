---
name: github-knowledge-card
description: Generate Chinese social-media-ready knowledge-map cover images and publishable summaries from one or more GitHub repository URLs. Use when the user provides GitHub project links and wants a 3:4 knowledge graph / infographic cover, Xiaohongshu or WeChat style content, suggested titles, project categorization, trend interpretation, rich long-form self-media copy, or concise Chinese copy for self-media.
---

# GitHub Knowledge Card

## Overview

Turn one or more GitHub repository URLs into a publishable Chinese self-media package: a 3:4 cover image concept or rendered asset, 3 suggested titles, and Chinese social-media copy.

Use a visual style similar to high-density Chinese AI infographic covers: bold oversized headline, dark tech background, purple/yellow accent contrast, segmented knowledge graph modules, icons, short labels, and a clear "why it matters" takeaway.

## Workflow

1. Parse all GitHub URLs and normalize them as `owner/repo`.
2. Gather repo facts from GitHub pages, API, `gh`, README files, release notes, stars, topics, license, primary language, recent activity, and docs. Browse or use GitHub tools when current facts matter.
3. For each repo, extract:
   - One-line positioning: what it is and who it helps.
   - Core capability: 3-5 short phrases.
   - Category: e.g. AI Agent, AI drawing/video, productivity tool, API/infrastructure, knowledge base, automation workflow, developer tool.
   - Signal: stars, update freshness, ecosystem fit, uniqueness, learning value.
4. Build a knowledge graph:
   - Single repo: center on the repo, branch into capabilities, workflow, use cases, stack, advantages, and adoption advice.
   - Multiple repos: group into 4-6 categories, place GitHub or the collection theme at center, connect categories to repo names and one short benefit each.
5. Produce the cover deliverable:
   - If the user asks for an actual image, use available image generation or render an HTML/PNG composition. Prefer 3:4 vertical output such as `1080x1440`.
   - If an image tool is unavailable or the user asks for prompt only, provide a detailed image prompt plus layout spec.
   - Treat the bottom summary strip as mandatory. The bottom 8-12% of the poster should contain a memorable formula, insight, or trend conclusion, not empty margin.
   - Fill the top-right quadrant. If there is no product screenshot, avatar, or generated character image, use a quote card, repo-signal card, mini workflow, GitHub badge cluster, or simple CSS illustration so the hero area feels complete.
6. Produce the copy deliverable:
   - 3 titles, each punchy and self-media friendly.
   - Default body: rich Chinese self-media copy in the user's example style, usually 700-1200 Chinese characters, with a hook, pain point, project explanation, workflow interpretation, trend insight, question, and hashtags.
   - If the user explicitly asks for "600 字以内", "简短", "摘要", or a specific platform limit, obey that limit.
   - Optional tags if appropriate.

## Research Rules

- Verify current GitHub facts instead of relying on memory. Stars, releases, maintainers, and repo activity can change.
- Prefer primary sources: the GitHub repo, README, docs, releases, discussions, package metadata, and official project sites.
- Do not overclaim. If a repo's status is unclear, phrase as "更适合探索/学习" instead of "生产可用".
- Keep repo descriptions short enough to fit inside the cover; move detail into the body copy.
- For Chinese self-media, prioritize usefulness and clarity over technical completeness.

## Cover Design Recipe (案例级小红书爆款图谱规范)

Read `references/cover-style.md` when creating an actual cover prompt or visual layout.

Default canvas & architecture:

- **Canvas**: 3:4 vertical (`1080x1440`), dark tech background (`#04060e` ~ `#080c20`) with 38px subtle grid lines and glowing borders.
- **Hero Title**: Double-line super visual hammer (White 80px + Bright Gold 82px), handwritten annotation with curved arrow at top-right, sub-strip with decorative lines.
- **Topological Paradigms** (Never use simple vertical card stacks!):
  1. *Paradigm A (Vertical Pipeline + Wings)*: Center 6-node colored pills with downward arrows, Left Wing for principles/checklists, Right Wing for pitfalls/reflections. (See `templates/template_vertical_pipeline.html`)
  2. *Paradigm B (Hub-and-Spoke)*: Center 3D Context Cube, Left inputs, Right outputs, curved luminous connectors.
  3. *Paradigm C (Decision Tree / Loop)*: Branching questions, multi-agent circular collaboration, self-healing loop.
- **Bottom Anchor**: Mandatory glowing lightbulb/quote card with an insight sentence + author signature bar. Zero dead zones at bottom.

## Output Format

Return the final answer in this order unless the user asks otherwise:

```markdown
## 封面图
[actual image path or detailed image prompt]

## 3 个标题
1. ...
2. ...
3. ...

## 正文
...

## 项目知识图谱
- Category: repo - short value
```

If creating files, save them in the current workspace with descriptive names such as `github-knowledge-card.png`, `github-knowledge-card.html`, or `github-knowledge-card.md`.

## Quality Bar

- The cover must communicate the topic within 2 seconds.
- The graph must show relationships, not just a list.
- Titles must feel clickable but not misleading.
- Body copy must match the requested length. If no length is requested, prefer a richer publishable post over a short abstract.
- Repo names must be spelled accurately.
- Avoid tiny paragraphs on the image; use labels and short phrases.
- Avoid dead zones: the top-right hero area and bottom summary area must both contain meaningful visual information.
- If facts are uncertain, disclose that the analysis is based on the checked repo materials.
