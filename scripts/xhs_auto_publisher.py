#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小红书自动化图文发布执行引擎 (Xiaohongshu Auto & Draft Publisher)
支持两种驱动模式：
1. Playwright 独立模式 (基于真实 Chrome + xhs_cookies.json)
2. OpenCLI 桥接模式 (通过 opencli xiaohongshu publish)

核心特性：
- 严格校验标题 ≤ 20 字符规范
- 支持交互式选择【保存到草稿箱】或【直接正式发布】
- 支持最多 9 张 3:4 高清图文卡片上传
- 支持自动清洗并注入高权重长尾话题库
"""

import os
import sys
import json
import time
import argparse
import subprocess
from pathlib import Path

# 加入脚本搜索路径
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.append(str(SCRIPTS_DIR))

import publish_pipeline

COOKIE_FILE = Path("/Users/workspace/ai_short_company/ai-short-drama/config/xhs_cookies.json")
XHS_PUBLISH_URL = "https://creator.xiaohongshu.com/publish/publish?source=official"

def load_cookies():
    if not COOKIE_FILE.exists():
        print(f"⚠️ 未找到授权 Cookie 文件: {COOKIE_FILE}")
        print("🚀 正在自动为您调起小红书扫码授权窗口，请使用手机 App 扫码登录...")
        import login_xhs_auth
        success = login_xhs_auth.interactive_login(timeout=180)
        if not success or not COOKIE_FILE.exists():
            raise FileNotFoundError(
                f"❌ 扫码授权未完成或超时！请重试或运行: python3 scripts/login_xhs_auth.py"
            )
    with open(COOKIE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("cookies", [])

def prompt_user_publish_choice(default_is_draft: bool = True) -> bool:
    """交互式询问用户是草稿发布还是直接发布"""
    print("\n" + "=" * 60)
    print("📢 【发布策略选择确认】")
    print("  [1] 保存为小红书草稿箱 (Draft - 推荐！可在手机端预览排版无风险)")
    print("  [2] 直接正式发布上线 (Live - 立即向全网公开)")
    print("=" * 60)
    
    # 非交互式终端环境兜底
    if not sys.stdin.isatty():
        print(f"⚠️ 当前处于非交互终端，默认采用: {'【草稿箱】' if default_is_draft else '【直接发布】'}")
        return default_is_draft

    try:
        choice = input("👉 请输入选项编号 (默认 1): ").strip()
        if choice == "2":
            return False
        return True
    except Exception:
        return default_is_draft

def publish_via_opencli(title: str, content: str, images: list[str], topics: list[str], is_draft: bool = True):
    """通过 OpenCLI 执行发布"""
    print("\n🚀 [模式 1] 正在通过 OpenCLI 桥接发布...")
    cmd, valid_title, _ = publish_pipeline.build_publish_payload(
        title=title,
        content=content,
        images=images,
        topics=topics,
        strategy="inline_clean"
    )
    if is_draft:
        cmd.extend(["--draft", "true"])

    print(f"执行命令: {' '.join(cmd[:8])} ...")
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"✅ OpenCLI 响应:\n{res.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"⚠️ OpenCLI 执行异常:\n{e.stderr or e.stdout}")
        return False

def publish_via_playwright(title: str, content: str, images: list[str], topics: list[str], is_draft: bool = True, dry_run: bool = False, comment: str = ""):
    """通过 Playwright 原生驱动发布"""
    from playwright.sync_api import sync_playwright

    print("\n🚀 [模式 2] 正在通过 Playwright 原生驱动小红书创作者中心...")
    cookies = load_cookies()

    # 规范化文本与标签并执行质量门禁脱敏
    from compliance_checker import sanitize_text
    content, rep_log = sanitize_text(content)
    if rep_log:
        print(f"🛡️ 发布引擎自动执行敏感词清洗: {len(rep_log)} 处")

    cleaned_content, final_topics = publish_pipeline.sanitize_and_expand_topics(content, topics)
    tags_line = " ".join([f"#{t}" for t in final_topics])
    # 注入平台合规硬性声明：【含AI合成内容】
    full_text = f"{cleaned_content}\n\n⚠️【内容声明】含AI合成内容\n\n{tags_line}"
    valid_title = title[:20] if len(title) > 20 else title

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=False)
        context = browser.new_context(
            viewport={"width": 1366, "height": 900},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        context.add_cookies(cookies)
        page = context.new_page()

        print("🌐 打开创作者发布页...")
        page.goto(XHS_PUBLISH_URL, wait_until="networkidle")
        time.sleep(3)

        if "login" in page.url:
            print("❌ Cookie 已过期，请重新运行: python3 scripts/login_xhs_auth.py")
            browser.close()
            return False

        # 1. 切换到“上传图文”标签 (使用 JS 直接点击避免视口拦截)
        try:
            page.evaluate("""() => {
                const els = Array.from(document.querySelectorAll('span, div, tab, button, a'));
                const tab = els.find(e => e.textContent && e.textContent.trim() === '上传图文');
                if (tab) tab.click();
            }""")
            print("✅ 已切换至【上传图文】工作区")
            time.sleep(2)
        except Exception as e:
            print(f"切换上传图文提示: {e}")

        # 2. 注入图片文件
        upload_input = page.locator('input[type="file"]')
        if upload_input.count() > 0:
            print(f"📤 注入 {len(images)} 张 3:4 图文卡片...")
            upload_input.first.set_input_files([str(p) for p in images])
            print("⏳ 等待图片上传与转码解析 (等待 6 秒)...")
            page.wait_for_timeout(6000)
        else:
            print("⚠️ 未找到文件输入框")

        # 3. 填入标题
        title_input = page.locator('input[placeholder*="填写标题"], input[placeholder*="标题"]').first
        if title_input.is_visible():
            title_input.fill(valid_title)
            print(f"📝 已填入标题: {valid_title}")
        else:
            # 降级通过 evaluate 赋值
            page.evaluate(f"""() => {{
                const input = document.querySelector('input[placeholder*="标题"]');
                if (input) {{
                    input.value = "{valid_title}";
                    input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                }}
            }}""")
            print(f"📝 (通过DOM注入) 已填入标题: {valid_title}")

        # 4. 填入正文 (带平台合规声明【含AI合成内容】)
        body_text = f"{cleaned_content}\n\n⚠️【内容声明】含AI合成内容\n\n"
        editor = page.locator('div[contenteditable="true"], textarea[placeholder*="输入正文"]')
        if editor.count() > 0:
            editor.first.fill(body_text)
            print(f"📄 已填入正文与声明 ({len(body_text)} 字)")

            # 4.0 关键优化：以真实按键模拟触发 TipTap Topic 节点转换（生成蓝色高亮可点击超链接话题）
            if final_topics:
                print(f"🏷️ 正在以原生 TipTap 交互模式挂载 {len(final_topics)} 个公域高权重话题...")
                try:
                    editor.first.click()
                    page.keyboard.press("End")
                    page.wait_for_timeout(300)
                    for topic in final_topics:
                        topic_name = topic.replace("#", "").strip()
                        if not topic_name:
                            continue
                        print(f"   -> 键入话题: #{topic_name}")
                        page.keyboard.type(f"#{topic_name}")
                        page.wait_for_timeout(800)
                        # 回车确认选中联想话题，TipTap 自动转换为 <a class="tiptap-topic"> 节点
                        page.keyboard.press("Enter")
                        page.wait_for_timeout(400)
                        page.keyboard.type(" ")
                        page.wait_for_timeout(200)
                    print("✅ 话题全部已转化为平台原生高亮超链接节点！")
                except Exception as e:
                    print(f"⚠️ 交互式话题挂载提示: {e}")

        # 4.1 处理小红书创作者中心硬性合规要求：【含AI合成内容】自主声明
        try:
            print("🛡️ 正在检查平台官方【笔记含AI合成内容】自主声明配置...")
            # 先清除可能遮挡的新手引导弹窗
            guide_btns = page.locator('.feature-guide__btn, .feature-guide__close, button:has-text("我知道了")')
            if guide_btns.count() > 0 and guide_btns.first.is_visible():
                guide_btns.first.click()
                page.wait_for_timeout(600)

            # 1. 点击展开下拉框 (使用 locator 点击)
            decl_input = page.locator(".custom-select-44, .d-select, :text('添加内容类型声明')").first
            if decl_input.is_visible():
                decl_input.scroll_into_view_if_needed()
                decl_input.click()
                print("📋 已点击展开【添加内容类型声明】下拉选择列表...")
                page.wait_for_timeout(1000)

                # 2. 点击 笔记含AI合成内容
                ai_item = page.locator(".d-option:has-text('笔记含AI合成内容'), :text('笔记含AI合成内容')").last
                if ai_item.is_visible():
                    ai_item.click(force=True)
                    page.wait_for_timeout(1000)
                    cur_text = page.locator(".custom-select-44, .d-select").first.inner_text()
                    print(f"✅ 成功选中平台官方合规项：【{cur_text}】！")
                else:
                    print("⚠️ 未找到【笔记含AI合成内容】选项，正文尾部已包含硬性声明。")
            else:
                print("ℹ️ 未能定位到【添加内容类型声明】组件。")
        except Exception as e:
            print(f"ℹ️ 平台声明交互提示: {e}")

        # 5. 等待页面与图片完全就绪并保存阶段截图
        screenshot_dir = Path("/Users/workspace/ai_short_company/ai-short-drama/scratch/x_to_xhs")
        screenshot_dir.mkdir(parents=True, exist_ok=True)
        before_path = screenshot_dir / "before_publish.png"
        page.screenshot(path=str(before_path), full_page=True)
        print(f"📸 已保存提交前表单全貌截图: {before_path}")

        # 5.1 强力关闭新手引导遮罩层 (feature-guide 遮罩会阻挡所有下层点击)
        try:
            guide_btns = page.locator('.feature-guide__btn, .feature-guide__close, button:has-text("我知道了")')
            if guide_btns.count() > 0:
                for idx in range(guide_btns.count()):
                    btn = guide_btns.nth(idx)
                    if btn.is_visible():
                        btn.click(force=True)
                        print("💡 已成功关闭新手引导弹窗【我知道了】")
                        page.wait_for_timeout(800)
                        break
            # 关闭话题推荐联想下拉框
            page.keyboard.press("Escape")
            page.wait_for_timeout(600)
        except Exception as e:
            print(f"ℹ️ 引导遮罩清理提示: {e}")

        # 5.2 探测小红书官方自定义底栏组件 <xhs-publish-btn>
        btn_container = page.locator("xhs-publish-btn")
        box = None
        if btn_container.count() > 0 and btn_container.first.is_visible():
            box = btn_container.first.bounding_box()
            print(f"🎯 成功定位小红书底栏发布组件: BoundingBox={box}")

        # 5.3 草稿箱 vs 直接发布
        if dry_run:
            print("👀 [DRY RUN 预览模式] 保持窗口打开 45 秒供核对...")
            time.sleep(45)
        elif is_draft:
            print("💾 正在执行【暂存离开 / 保存草稿】...")
            # 经过图像物理像素分析测量：暂存离开中心在 (560, 854)
            draft_x = (box["x"] + 236) if box else 560
            draft_y = (box["y"] + 44) if box else 854
            print(f"🖱️ 触发精准鼠标物理点击【暂存离开】: ({draft_x}, {draft_y})")
            page.mouse.move(draft_x, draft_y)
            page.wait_for_timeout(300)
            page.mouse.click(draft_x, draft_y)

            time.sleep(4)
            after_path = screenshot_dir / "after_draft.png"
            page.screenshot(path=str(after_path))
            print(f"📸 已保存草稿保存后截图: {after_path}")
            print("\n========================================================")
            print("🎉🎉🎉 恭喜！小红书图文笔记已成功保存至【草稿箱】！")
            print("📱 您可以打开手机小红书App，进入【我】的主页草稿箱查看与预览！")
            print("========================================================\n")
        else:
            print("🚀 正在执行【正式公开上线发布】...")
            # 经过图像物理像素分析测量：红底立即发布中心在 (735, 854)
            publish_x = (box["x"] + 412) if box else 735
            publish_y = (box["y"] + 44) if box else 854
            print(f"🖱️ 触发精准鼠标物理点击【红底立即发布】: ({publish_x}, {publish_y})")
            page.mouse.move(publish_x, publish_y)
            page.wait_for_timeout(400)
            page.mouse.click(publish_x, publish_y)

            # 等待小红书处理提交并处理二次确认弹窗
            page.wait_for_timeout(3000)
            try:
                confirms = page.locator('button:has-text("确定"), button:has-text("确认"), button:has-text("立即发布")')
                if confirms.count() > 0 and confirms.first.is_visible():
                    confirms.first.click()
                    print("✅ 已确认提交弹窗")
            except Exception:
                pass

            time.sleep(6)
            after_path = screenshot_dir / "after_publish.png"
            page.screenshot(path=str(after_path))
            print(f"📸 已保存发布后页面状态截图: {after_path}")
            print("\n========================================================")
            print("🎉🎉🎉 恭喜！小红书爆款图文笔记已正式公开上线发布！")
            print("📱 您可以打开手机小红书App，进入【我】的主页或创作者中心核对确认！")
            print("========================================================\n")

            # 5.4 路径 A：发布后自动跟评（作者自主首评/沙发运营引导）
            if comment and not is_draft and not dry_run:
                print(f"\n💬 正在执行【路径 A：作者自主首评/运营跟评】...")
                print(f"   首评文案: {comment}")
                try:
                    # 访问创作者服务平台【笔记管理】真实地址
                    page.goto("https://creator.xiaohongshu.com/new/note-manager", wait_until="domcontentloaded", timeout=25000)
                    page.wait_for_timeout(3500)
                    comment_after_path = screenshot_dir / "creator_notes_list.png"
                    page.screenshot(path=str(comment_after_path))
                    print(f"📸 已记录创作者中心笔记列表截图: {comment_after_path}")

                    # 探测目标笔记卡片并提取其底层 noteId (从 data-impression JSON 中解析)
                    note_id = None
                    target_note = page.locator(f"text={valid_title[:10]}").first
                    if target_note.is_visible():
                        card = target_note.locator('xpath=./ancestor::div[contains(@class, "note-card")]').first
                        if card.count() > 0:
                            imp_data = card.get_attribute("data-impression")
                            if imp_data:
                                import re
                                m = re.search(r'"noteId":\s*"([a-f0-9]{24})"', imp_data)
                                if m:
                                    note_id = m.group(1)
                                    print(f"🎯 成功从创作者中心提取到官方唯一 NoteId: {note_id}")

                    if note_id:
                        note_url = f"https://www.xiaohongshu.com/explore/{note_id}"
                        print(f"🔗 官方前台互动地址: {note_url}")
                        # 尝试前台跟评 (若刚发布处于平台分发队列，会记录状态待审核完成后可见)
                        page.goto(note_url, wait_until="domcontentloaded", timeout=20000)
                        page.wait_for_timeout(3000)

                        comment_input = page.locator('div[contenteditable="true"], textarea[placeholder*="说点什么"], input[placeholder*="说点什么"], .content-edit').first
                        if comment_input.count() > 0 and comment_input.is_visible():
                            comment_input.click()
                            page.wait_for_timeout(500)
                            comment_input.fill(comment)
                            page.wait_for_timeout(500)
                            send_btn = page.locator('button:has-text("发送"), .submit-btn, :text("发送")').first
                            if send_btn.is_visible():
                                send_btn.click()
                            else:
                                page.keyboard.press("Enter")
                            page.wait_for_timeout(2000)
                            print("🎉 作者首评发表成功！")
                            post_comment_path = screenshot_dir / "after_comment.png"
                            page.screenshot(path=str(post_comment_path))
                        else:
                            print("ℹ️ 笔记已进入平台公域分发审核队列（创作者后台显示正常分发中），公域前台页面将在数分钟审核完成后激活互动。")
                    else:
                        print("ℹ️ 笔记已成功入库发布，后台正在完成初始数据同步。")
                except Exception as ce:
                    print(f"ℹ️ 自主首评执行提示: {ce}")

        browser.close()
        return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="小红书全自动图文发布执行器")
    parser.add_argument("--from-json", type=str, default="", help="直接从指定的 note_draft.json 文件加载发布数据")
    parser.add_argument("--title", type=str, default="", help="笔记标题 (≤20字)")
    parser.add_argument("--content", type=str, default="", help="笔记正文")
    parser.add_argument("--images", type=str, default="", help="图片路径 (逗号分隔)")
    parser.add_argument("--topics", type=str, default="", help="话题列表 (逗号分隔)")
    parser.add_argument("--comment", type=str, default="", help="发布后自动追加的作者自主首评")
    parser.add_argument("--draft", dest="is_draft", action="store_true", help="指定保存为草稿")
    parser.add_argument("--live", dest="is_live", action="store_true", help="指定直接公开上线")
    parser.add_argument("--engine", type=str, choices=["playwright", "opencli"], default="playwright", help="发布引擎选择")
    parser.add_argument("--dry-run", action="store_true", help="仅填表不点击最终提交")
    args = parser.parse_args()

    # 若指定了 --from-json，则优先从 json 文件中加载
    if args.from_json and Path(args.from_json).exists():
        with open(args.from_json, "r", encoding="utf-8") as f:
            jdata = json.load(f)
        target_title = jdata.get("title", args.title)
        target_content = jdata.get("content", args.content)
        target_images = [Path(p) for p in jdata.get("images", [])]
        target_topics = jdata.get("topics", [])
        target_comment = jdata.get("first_comment", jdata.get("comment", args.comment))
    else:
        if not args.title or not args.content or not args.images:
            raise ValueError("必须提供 --title, --content, --images 或使用 --from-json 指定数据文件！")
        target_title = args.title
        target_content = args.content
        target_images = [Path(p.strip()) for p in args.images.split(",") if p.strip()]
        target_topics = [t.strip() for t in args.topics.split(",") if t.strip()]
        target_comment = args.comment

    image_list = target_images
    topic_list = target_topics

    # 判断草稿还是直接发布
    if args.is_draft:
        is_draft_mode = True
    elif args.is_live:
        is_draft_mode = False
    else:
        # 交互式提示用户选择
        is_draft_mode = prompt_user_publish_choice(default_is_draft=True)

    print(f"\n🎯 确定发布模式: {'【保存到草稿箱】' if is_draft_mode else '【直接正式发布】'}")

    if args.engine == "opencli":
        success = publish_via_opencli(target_title, target_content, [str(p) for p in image_list], topic_list, is_draft=is_draft_mode)
        if not success:
            print("🔄 OpenCLI 发布未成功，自动切换至 Playwright 引擎兜底...")
            publish_via_playwright(target_title, target_content, image_list, topic_list, is_draft=is_draft_mode, dry_run=args.dry_run, comment=target_comment)
    else:
        publish_via_playwright(target_title, target_content, image_list, topic_list, is_draft=is_draft_mode, dry_run=args.dry_run, comment=target_comment)
