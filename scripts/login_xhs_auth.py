#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小红书创作者中心登录授权与 Cookie 捕获提取工具 (Xiaohongshu Auth & Cookie Capturer)

支持两种授权接入方式：
1. 本地弹窗扫码交互授权 (推荐)：
   调用系统 Chrome 打开小红书创作者服务平台，在屏幕上展示扫码界面。
   用户手机小红书 App 扫码确认后，自动捕获登录凭证并持久化保存。
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
COOKIE_FILE = COOKIE_DIR / "xhs_cookies.json"
XHS_LOGIN_URL = "https://creator.xiaohongshu.com/"

def save_cookies(cookies_list: list, local_storage: dict = None):
    """保存 Cookie 为标准 JSON 格式供自动化发布脚本复用"""
    COOKIE_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "cookies": cookies_list,
        "local_storage": local_storage or {}
    }
    with open(COOKIE_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"🎉 成功持久化保存小红书登录凭证至: {COOKIE_FILE}")

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
                "domain": ".xiaohongshu.com",
                "path": "/"
            })
    save_cookies(cookies_list)

def interactive_login(timeout: int = 180):
    """通过 Playwright 启动系统 Chrome 弹窗，引导用户扫码并自动抓取"""
    from playwright.sync_api import sync_playwright

    print("=" * 60)
    print("🚀 正在启动系统 Chrome 浏览器，准备小红书扫码授权...")
    print("=" * 60)
    print(f"🔗 目标登录页: {XHS_LOGIN_URL}")
    print("👉 请在稍后弹出的浏览器窗口中，使用【小红书 App】扫码完成登录。")
    print(f"⏱️ 登录监听等待中 (最长等待 {timeout} 秒)...")

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=False)
        context = browser.new_context(
            viewport={"width": 1280, "height": 850},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        page.goto(XHS_LOGIN_URL)

        start_time = time.time()
        is_logged_in = False

        while time.time() - start_time < timeout:
            current_url = page.url
            cookies = context.cookies()
            cookie_names = [c["name"] for c in cookies]
            
            # 检测关键授权鉴权 Cookie，例如 web_session / a1 / customer-sso-sid / xsecappid
            has_session = any(name in ["web_session", "customer-sso-sid", "xsecappid"] for name in cookie_names)
            
            # 创作者后台成功进入首页特征
            if "creator/home" in current_url or "publish" in current_url or (has_session and "login" not in current_url):
                print("\n✅ 检测到已成功登录小红书创作者服务平台！")
                save_cookies(cookies)
                is_logged_in = True
                time.sleep(2)
                break
                
            time.sleep(1.5)

        browser.close()

        if not is_logged_in:
            print("\n❌ 登录等待超时或未检测到有效会话，请重试。")
            return False
        return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="小红书登录授权工具")
    parser.add_argument("--cookie-str", type=str, help="直接导入 document.cookie 文本")
    parser.add_argument("--timeout", type=int, default=180, help="扫码超时等待时间(秒)")
    args = parser.parse_args()

    if args.cookie_str:
        parse_and_save_raw_cookie_str(args.cookie_str)
    else:
        interactive_login(timeout=args.timeout)
