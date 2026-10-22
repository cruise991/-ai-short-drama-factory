#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抖音创作者中心登录授权与 Cookie 捕获提取工具 (Douyin Auth & Cookie Capturer)

支持两种授权接入方式：
1. 本地弹窗扫码交互授权 (推荐)：
   调用系统 Chrome 打开抖音创作者服务平台，在屏幕上展示扫码界面。
   用户手机抖音 App 扫码确认后，自动捕获登录凭证并持久化保存。
2. 文本导入方式：
   若在日常浏览器已登录，可通过 --cookie-str 快速载入保存。
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path

COOKIE_DIR = Path("/Users/workspace/ai_short_company/ai-short-drama/config")
COOKIE_FILE = COOKIE_DIR / "douyin_cookies.json"
DOUYIN_LOGIN_URL = "https://creator.douyin.com/"

def save_cookies(cookies_list: list, local_storage: dict = None):
    """保存 Cookie 为标准 JSON 格式供自动化脚本复用"""
    COOKIE_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "cookies": cookies_list,
        "local_storage": local_storage or {}
    }
    with open(COOKIE_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"🎉 成功持久化保存抖音登录凭证至: {COOKIE_FILE}")

def parse_and_save_raw_cookie_str(raw_str: str):
    """将浏览器 DevTools / document.cookie 格式的字符串解析为 Cookie 列表"""
    cookies_list = []
    items = raw_str.strip().split(";")
    for item in items:
        if "=" in item:
            name, value = item.strip().split("=", 1)
            cookies_list.append({
                "name": name,
                "value": value,
                "domain": ".douyin.com",
                "path": "/"
            })
    save_cookies(cookies_list)

def interactive_login(timeout: int = 180):
    """通过 Playwright 启动 Chrome 弹窗，引导用户扫码并自动抓取"""
    from playwright.sync_api import sync_playwright

    print("=" * 60)
    print("🚀 正在启动系统 Chrome 浏览器，准备抖音扫码授权...")
    print("=" * 60)
    print(f"🔗 目标登录页: {DOUYIN_LOGIN_URL}")
    print("👉 请在稍后弹出的浏览器窗口中，使用【抖音 App】扫码完成登录。")
    print(f"⏱️ 登录监听等待中 (最长等待 {timeout} 秒)...")

    with sync_playwright() as p:
        # 使用系统的 Google Chrome
        browser = p.chromium.launch(channel="chrome", headless=False)
        context = browser.new_context(
            viewport={"width": 1280, "height": 850},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        page.goto(DOUYIN_LOGIN_URL)

        start_time = time.time()
        is_logged_in = False

        while time.time() - start_time < timeout:
            current_url = page.url
            # 抖音创作者中心登录成功后通常会跳转到 /creator-micro/ 路径
            cookies = context.cookies()
            cookie_names = [c["name"] for c in cookies]
            
            # 检测关键授权鉴权 Cookie，例如 sessionid / passport_auth
            has_session = any("sessionid" in name or "passport_auth" in name for name in cookie_names)
            
            if "creator-micro" in current_url or has_session:
                print("\n✅ 检测到已成功登录抖音创作者中心！")
                save_cookies(cookies)
                is_logged_in = True
                # 停留 2 秒确保后续页面数据同步
                time.sleep(2)
                break
                
            time.sleep(1.5)

        browser.close()

        if not is_logged_in:
            print("\n❌ 登录等待超时或未检测到有效会话，请重试。")
            return False
            
        return True

def main():
    parser = argparse.ArgumentParser(description="抖音创作者中心登录与 Cookie 授权工具")
    parser.add_argument("--cookie-str", type=str, default=None, help="直接导入 document.cookie 格式的字符串")
    parser.add_argument("--timeout", type=int, default=180, help="扫码登录等待超时时间(秒)")
    args = parser.parse_args()

    if args.cookie_str:
        print("📥 正在解析并保存手动输入的 Cookie 字符串...")
        parse_and_save_raw_cookie_str(args.cookie_str)
    else:
        interactive_login(timeout=args.timeout)

if __name__ == "__main__":
    main()
