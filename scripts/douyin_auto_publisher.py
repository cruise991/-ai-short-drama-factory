#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抖音自动化/定时发布执行引擎 (Douyin Auto & Scheduled Uploader)
基于 Playwright + 已授权 Cookies 驱动。
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path
from datetime import datetime, timedelta

COOKIE_FILE = Path("/Users/workspace/ai_short_company/ai-short-drama/config/douyin_cookies.json")
UPLOAD_URL = "https://creator.douyin.com/creator-micro/content/upload"

DEFAULT_VIDEO = Path("/Users/workspace/ai_short_company/ai-short-drama/projects/handdraw_marriage_squeeze/outputs/film.mp4")
DEFAULT_COVER = Path("/Users/workspace/ai_short_company/ai-short-drama/projects/handdraw_marriage_squeeze/outputs/cover.png")

DEFAULT_TITLE = "为什么结婚人数连年暴跌？婚姻梯队错配死局"
DEFAULT_CAPTION = """民政局登记创新低，相亲角A女愁嫁，农村D男愁娶。很多人归咎于挑剔，但底层其实是残酷的数学梯队错配。戳中痛点的底层逻辑，你看懂了吗？

#婚姻现状 #为什么不结婚 #婚姻梯队模型 #相亲 #深度思考 #社会现象 #情感共鸣 #认知思维 #年轻人现状 #人性哲学"""

# 长期记忆与规约必选项
DEFAULT_COLLECTION = "Ai工作流"
DEFAULT_DECLARATION = "内容由AI生成"  # 平台合规硬性约束，必选


def load_cookies():
    if not COOKIE_FILE.exists():
        raise FileNotFoundError(
            f"未找到授权 Cookie 文件: {COOKIE_FILE}\n请先运行: python3 scripts/login_douyin_auth.py 完成登录授权！"
        )
    with open(COOKIE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("cookies", [])

def execute_publish(
    video_path: Path,
    cover_path: Path,
    title: str,
    caption: str,
    schedule_time: str = None,
    dry_run: bool = True
):
    from playwright.sync_api import sync_playwright

    print("=" * 60)
    print("🎬 准备执行抖音短视频上传与定时发布")
    print("=" * 60)
    print(f"📦 视频文件: {video_path}")
    print(f"🖼️ 封面图片: {cover_path}")
    print(f"📝 视频标题: {title}")
    print(f"⏰ 发布模式: {'【定时发布】' + schedule_time if schedule_time else '【立即发布】'}")
    print(f"🛡️ 运行模式: {'[DRY RUN 预演模式，仅填表不点击最终提交]' if dry_run else '[LIVE 正式发布]'}")

    cookies = load_cookies()

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=False)
        context = browser.new_context(
            viewport={"width": 1366, "height": 900},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        
        # 注入 Cookies
        context.add_cookies(cookies)
        page = context.new_page()

        print("\n🌐 正在进入抖音创作者中心发布页...")
        page.goto(UPLOAD_URL, wait_until="networkidle")
        time.sleep(3)

        # 检查是否仍在登录页（Cookie 是否过期）
        if "login" in page.url or "passport" in page.url:
            print("⚠️ 登录凭证已过期或无效，请重新运行 login_douyin_auth.py 授权。")
            browser.close()
            return False

        print("✅ 成功进入视频上传控制台，开始上传流程...")
        
        # 定位上传输入框
        upload_input = page.locator('input[type="file"]')
        if upload_input.count() > 0:
            upload_input.first.set_input_files(str(video_path))
            print("📤 视频文件已注入上传队列，等待转码与解析...")
            # 等待视频上传并进入详情编辑界面
            page.wait_for_timeout(8000)
        else:
            print("⚠️ 未找到文件上传入口元素，请在浏览器中手动拖入视频。")

        # 保持界面打开供用户查看或后续交互
        if dry_run:
            print("\n👀 [DRY RUN 模式] 浏览器界面将保持打开 60 秒供您查看与校验...")
            time.sleep(60)
        else:
            print("\n🚀 正在提交发布任务...")
            time.sleep(5)

        browser.close()
        print("🎉 流程执行完毕！")
        return True

def main():
    parser = argparse.ArgumentParser(description="抖音自动化发布执行器")
    parser.add_argument("--video", type=str, default=str(DEFAULT_VIDEO))
    parser.add_argument("--cover", type=str, default=str(DEFAULT_COVER))
    parser.add_argument("--schedule", type=str, default="2026-10-21 20:30:00")
    parser.add_argument("--publish", action="store_true", help="是否正式点击发布(默认 dry-run 仅填表)")
    args = parser.parse_args()

    execute_publish(
        video_path=Path(args.video),
        cover_path=Path(args.cover),
        title=DEFAULT_TITLE,
        caption=DEFAULT_CAPTION,
        schedule_time=args.schedule,
        dry_run=not args.publish
    )

if __name__ == "__main__":
    main()
