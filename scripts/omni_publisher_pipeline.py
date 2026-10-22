#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全渠道自媒体内容流水线统一执行引擎 (Omnichannel Social Media Pipeline)
整合：小红书 (Xiaohongshu) + 抖音 (Douyin)
全链路涵盖：
1. [多源嗅探与选题蒸馏]：输入网页URL、X链接或纯文本，提炼核心商业卡点与高转化选题；
2. [文案改写与平台对齐]：标题 ≤20 字限制、痛点引入、正文去标识化、SEO长尾话题注入；
3. [图文/视频视觉生产]：3:4 满幅纯矢量 HTML 卡片渲染 / 9:16 短视频生成，严格 0% 拉伸失真；
4. [统一前置质量门禁]：compliance_checker 自动化静态审计（防限流、防断头、平台中性词替换）；
5. [双平台发布与AI声明]：小红书 TipTap 原生蓝色超链接话题、官方【含AI合成内容】声明勾选；抖音【内容由AI生成】声明与合集挂载；
6. [作者自主首评闭环]：发布后自动执行评论区沙发运营首评置顶互动。
"""

import os
import sys
import json
import time
import argparse
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = Path(__file__).resolve().parent
PROJECTS_DIR = BASE_DIR / "projects"
CONFIG_DIR = BASE_DIR / "config"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.append(str(SCRIPTS_DIR))

import compliance_checker
import publish_pipeline

def detect_input_type(input_str: str) -> str:
    """自动判断输入是 URL、文件路径还是原始文本"""
    s = input_str.strip()
    if s.startswith("http://") or s.startswith("https://"):
        return "url"
    if Path(s).exists():
        return "file"
    return "text"

def run_omni_pipeline(
    input_content: str,
    platform: str = "xhs",
    mode: str = "interactive",
    media_type: str = "auto",
    project_slug: str = None,
    comment_text: str = None,
    schedule_time: str = None,
    dry_run: bool = False
):
    print("=" * 70)
    print("🌟 【全渠道自媒体自动化发布与运营系统 (Omni-Publisher Pipeline)】")
    print(f"🎯 目标平台: {platform.upper()}")
    print(f"📦 输入类型: {detect_input_type(input_content)}")
    print(f"🚀 发布模式: {mode} (dry_run={dry_run})")
    print("=" * 70)

    # 1. 规范化工程目录
    if not project_slug:
        project_slug = f"project_{int(time.time())}"
    proj_dir = PROJECTS_DIR / project_slug
    proj_dir.mkdir(parents=True, exist_ok=True)
    img_dir = proj_dir / "images"
    img_dir.mkdir(parents=True, exist_ok=True)
    draft_file = proj_dir / "note_draft.json"

    print(f"📁 当前工作目录: {proj_dir}")

    # 2. 如果存在既有 draft，加载或重新构建
    note_data = {}
    if draft_file.exists():
        with open(draft_file, "r", encoding="utf-8") as f:
            note_data = json.load(f)
        print(f"📄 成功加载既有稿件配置: 《{note_data.get('title')}》")
    else:
        print("💡 未检测到本地稿件配置，可通过 LLM 或输入源实时生成 note_draft.json 后继续执行。")

    # 3. 质量门禁静态审计 (Compliance Gate)
    if note_data:
        print("\n🛡️ 正在执行发布前置质量门禁 (Compliance Quality Gate)...")
        title = note_data.get("title", "")
        content = note_data.get("content", "")
        images = [Path(p) for p in note_data.get("images", [])]
        html_templates = [Path(p) for p in note_data.get("html_templates", [])]

        report = compliance_checker.audit_package(
            title=title,
            text_content=content,
            image_paths=images,
            html_templates=html_templates
        )

        passed, issues = compliance_checker.format_audit_report(report)
        print(issues)
        if not passed:
            print("❌ 质量门禁未通过，发布管道自动阻断！请修正后重试。")
            return False
        print("✅ 质量门禁 100% 满分通过！准许放行发布。")

    # 4. 根据目标平台执行发布
    if platform in ["xhs", "all"]:
        print("\n" + "-" * 50)
        print("📕 正在启动【小红书】自动化发布引擎 (xhs_auto_publisher)...")
        print("-" * 50)
        xhs_cmd = [
            sys.executable,
            str(SCRIPTS_DIR / "xhs_auto_publisher.py"),
            "--from-json", str(draft_file)
        ]
        if mode == "draft":
            xhs_cmd.append("--draft")
        elif mode == "live":
            xhs_cmd.append("--live")
        if dry_run:
            xhs_cmd.append("--dry-run")
        if comment_text:
            xhs_cmd.extend(["--comment", comment_text])

        res = subprocess.run(xhs_cmd)
        if res.returncode != 0:
            print("⚠️ 小红书发布执行异常，退出码:", res.returncode)
        else:
            print("🎉 小红书发布流程执行完毕！")

    if platform in ["douyin", "all"]:
        print("\n" + "-" * 50)
        print("🎵 正在启动【抖音】自动化发布引擎 (douyin_auto_publisher)...")
        print("-" * 50)
        # 准备抖音发布命令
        dy_video = note_data.get("video_path")
        dy_cover = images[0] if images else None
        if not dy_video:
            print("ℹ️ 抖音发布通常需要 mp4 视频文件。若当前为图文卡片，可将其转为动效视频或使用图文模式。")
        else:
            dy_cmd = [
                sys.executable,
                str(SCRIPTS_DIR / "douyin_auto_publisher.py"),
                "--video", str(dy_video),
                "--cover", str(dy_cover) if dy_cover else "",
                "--title", note_data.get("title", ""),
                "--caption", note_data.get("content", "")
            ]
            if schedule_time:
                dy_cmd.extend(["--schedule", schedule_time])
            if dry_run:
                dy_cmd.append("--dry-run")
            subprocess.run(dy_cmd)

    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="全渠道自媒体自动化发布与运营系统")
    parser.add_argument("--input", type=str, required=True, help="输入源 (URL、文件路径或文本内容)")
    parser.add_argument("--platform", type=str, choices=["xhs", "douyin", "all"], default="xhs", help="目标平台")
    parser.add_argument("--mode", type=str, choices=["draft", "live", "interactive"], default="interactive", help="发布模式")
    parser.add_argument("--media-type", type=str, choices=["images", "video", "auto"], default="auto", help="媒体形态")
    parser.add_argument("--project", type=str, default="", help="项目名 slug")
    parser.add_argument("--comment", type=str, default="", help="作者自主首评")
    parser.add_argument("--schedule", type=str, default="", help="定时发布时间 (YYYY-MM-DD HH:MM)")
    parser.add_argument("--dry-run", action="store_true", help="预演模式不提交")
    args = parser.parse_args()

    run_omni_pipeline(
        input_content=args.input,
        platform=args.platform,
        mode=args.mode,
        media_type=args.media_type,
        project_slug=args.project or None,
        comment_text=args.comment or None,
        schedule_time=args.schedule or None,
        dry_run=args.dry_run
    )
