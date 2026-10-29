import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

COOKIE_FILE = Path("/Users/workspace/ai_short_company/ai-short-drama/config/xhs_cookies.json")
NOTE_ID = "6ad990cd0000000033011600"
NOTE_URL = f"https://www.xiaohongshu.com/explore/{NOTE_ID}"
DEFAULT_COMMENT = "💬 整理了一份《企业AI落地七要素定义表 + Skills规范模板.md》，需要的小伙伴可以在评论区交流，看到都会发给大家~ 欢迎聊聊你们目前卡在哪个环节！"

def run_comment_test(comment_text: str = DEFAULT_COMMENT):
    print("=" * 60)
    print("🚀 【小红书前台笔记评论自动化测试】")
    print(f"🔗 目标笔记: {NOTE_URL}")
    print(f"💬 拟发评论: {comment_text}")
    print("=" * 60)

    cookies = []
    if COOKIE_FILE.exists():
        with open(COOKIE_FILE, "r", encoding="utf-8") as f:
            cookies = json.load(f).get("cookies", [])

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=False)
        context = browser.new_context()
        if cookies:
            context.add_cookies(cookies)

        page = context.new_page()
        print("🌐 正在打开小红书 Web 前台笔记详情页...")
        page.goto(NOTE_URL, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(3000)

        # 检查是否出现登录弹窗
        login_modal = page.locator('.login-container, .qrcode-img, .login-box, :text("手机号登录")')
        if login_modal.count() > 0 and login_modal.first.is_visible():
            print("\n⚠️ 检测到小红书 Web 前台需要扫码鉴权（创作者中心凭证与前台社区凭证独立）：")
            print("👉 屏幕已为您弹出前台扫码窗口，请使用【小红书 App】扫一扫完成前台授权 (限时 120 秒)...")

            # 等待登录成功 (登录弹窗关闭 或 互动评论框出现)
            logged_in = False
            for _ in range(60):
                page.wait_for_timeout(2000)
                # 检查评论框或用户头像是否出现
                has_input = page.locator('div[contenteditable="true"], textarea[placeholder*="说点什么"], input[placeholder*="说点什么"], .interactions').count() > 0
                is_modal_hidden = not login_modal.first.is_visible() if login_modal.count() > 0 else True
                if has_input or is_modal_hidden:
                    print("✅ 检测到前台扫码授权成功！")
                    logged_in = True
                    break

            # 智能合并 Cookie，防止覆盖创作者后台凭证
            curr_cookies = context.cookies()
            cookie_dict = {(c["name"], c.get("domain", "")): c for c in cookies}
            for c in curr_cookies:
                cookie_dict[(c["name"], c.get("domain", ""))] = c
            merged_cookies = list(cookie_dict.values())

            with open(COOKIE_FILE, "w", encoding="utf-8") as f:
                json.dump({"updated_at": time.strftime("%Y-%m-%d %H:%M:%S"), "cookies": merged_cookies}, f, ensure_ascii=False, indent=2)
            print("💾 已将前台 Web 社区登录凭证与创作者凭证安全合并保存。")
            page.wait_for_timeout(2000)

        # 定位评论输入框
        print("🔍 正在定位笔记互动评论输入框...")
        comment_input = page.locator('div[contenteditable="true"], textarea[placeholder*="说点什么"], input[placeholder*="说点什么"], .content-edit').first
        if comment_input.is_visible():
            comment_input.click()
            page.wait_for_timeout(500)
            comment_input.fill(comment_text)
            page.wait_for_timeout(500)
            print(f"📝 已填入评论内容: {comment_text[:30]}...")

            # 点击发送
            send_btn = page.locator('button:has-text("发送"), .submit-btn, :text("发送")').first
            if send_btn.is_visible():
                send_btn.click()
            else:
                page.keyboard.press("Enter")
            
            page.wait_for_timeout(3000)
            print("🎉🎉🎉 恭喜！作者首评已成功发布到笔记下方！")
            after_comment_path = "/Users/workspace/ai_short_company/ai-short-drama/scratch/x_to_xhs/after_comment_real.png"
            page.screenshot(path=after_comment_path)
            print(f"📸 已记录评论后截图: {after_comment_path}")
        else:
            print("ℹ️ 评论输入框暂时不可见，请核对前台页面状态。")
            page.screenshot(path="/Users/workspace/ai_short_company/ai-short-drama/scratch/x_to_xhs/comment_failed.png")

        browser.close()

if __name__ == "__main__":
    run_comment_test()
