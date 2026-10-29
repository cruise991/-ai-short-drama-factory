#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小红书自动化发布标准中间件 (Topic Sanitizer & Publication Pipeline)
解决两大痛点：
1. 正文手写话题与 CLI --topics 冲突导致的重复粘连；
2. 自动扩充长尾高权重流量词库，对标小红书爆款排版。
"""

import re
import subprocess
import json
import os
import sys

def sanitize_and_expand_topics(raw_content: str, custom_topics: list = None) -> tuple[str, list[str]]:
    """
    1. 剥离正文末尾的手写 #话题 标签，防止与系统注入冲突；
    2. 扩充高质量长尾词，生成规范的 10 个话题标签列表。
    """
    # 正则剥离末尾连续的 #话题
    cleaned_content = re.sub(r'(\s*#[^\s#]+)+\s*$', '', raw_content.strip()).strip()

    # 高频 SEO 爆款长尾词库 (与用户人工修复的图2风格对标)
    seo_pool = [
        "AI工作流", "自媒体运营", "自动化工具", "独立开发", "干货分享",
        "AI工具", "人工智能", "自媒体工具", "开发者选项", "效率神器"
    ]

    # 合并、保序去重并限制在 10 个以内
    combined = list(dict.fromkeys((custom_topics or []) + seo_pool))[:10]
    return cleaned_content, combined

def build_publish_payload(title: str, content: str, images: list[str], topics: list[str], strategy: str = "cli_param"):
    """
    构建安全的发布指令。
    strategy:
      - 'cli_param' (默认推荐): 正文纯文本，通过 --topics 参数交给 opencli 处理
      - 'inline_clean' (容灾方案): 命令行不传 --topics，直接在正文末尾优雅拼接单行空格隔开的话题
    """
    # 强制标题 ≤ 20 字符
    if len(title) > 20:
        title = title[:20]

    # 校验并过滤图片路径
    valid_images = [img for img in images if os.path.exists(img)]
    if not valid_images:
        raise FileNotFoundError("未找到有效的待发布图片！")

    if strategy == "inline_clean":
        # 正文末尾追加单行空格分隔的优雅话题行（杜绝换行和竖排）
        tags_line = " ".join([f"#{t}" for t in topics])
        final_content = f"{content}\n\n{tags_line}"
        cmd = [
            "npx", "-y", "@jackwener/opencli", "xiaohongshu", "publish",
            final_content,
            "--title", title,
            "--images", ",".join(valid_images),
            "-f", "json"
        ]
    else:
        # 纯净正文 + --topics 参数
        cmd = [
            "npx", "-y", "@jackwener/opencli", "xiaohongshu", "publish",
            content,
            "--title", title,
            "--images", ",".join(valid_images),
            "--topics", ",".join(topics),
            "-f", "json"
        ]

    return cmd, title, len(title)

if __name__ == "__main__":
    # 测试用例：模拟包含脏话题的正文
    sample_raw = """一人自媒体也能跑出工业级流水线，欢迎交流你的自动化方案～

#AI工作流 #自媒体运营 #自动化工具 #独立开发 #干货分享"""

    cleaned, final_topics = sanitize_and_expand_topics(sample_raw)
    print("--- 清洗后的正文末尾 ---")
    print(cleaned[-60:])
    print("\n--- 智能扩充并去重后的 10 个话题 ---")
    print(" ".join([f"#{t}" for t in final_topics]))
    
    cmd, title, tlen = build_publish_payload(
        title="AI全自动发布！6大工具实战图解",
        content=cleaned,
        images=["/Users/workspace/ai_short_company/ai-short-drama/projects/ai_workflow_sharing/images/cover_workflow_pub_v2.jpg"],
        topics=final_topics,
        strategy="inline_clean"
    )
    print("\n--- 构建的合规命令 ---")
    print(" ".join(cmd[:8]) + " ...")
