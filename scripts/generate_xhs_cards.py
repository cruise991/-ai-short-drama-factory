#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小红书 3:4 满幅爆款图文卡片生成器 (Xiaohongshu 3:4 Carousel Card Generator)
利用本地 Playwright + 真实案例截图 + 商业杂志排版，1秒直出无损 1080x1440 PNG 组图。
"""

import os
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "scratch/x_to_xhs/raw_images"
DEFAULT_OUT_DIR = BASE_DIR / "projects/ai_beauty_monetization/images"

def generate_all_cards(output_dir: Path = DEFAULT_OUT_DIR):
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"🎨 正在渲染 4 张小红书 3:4 (1080x1440) 满幅合规图文卡片至: {output_dir}")

    cover_html = BASE_DIR / "scratch/x_to_xhs/magazine_cover_with_real_img.html"
    tasks = [
        (1, "card_01_cover", cover_html),
        (2, "card_02_detail_a", output_dir / "card_02_detail_a.html"),
        (3, "card_03_detail_b", output_dir / "card_03_detail_b.html"),
        (4, "card_04_sop_compliance", output_dir / "card_04_sop_compliance.html"),
    ]

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        for num, name, html_file in tasks:
            png_file = output_dir / f"{name}.png"
            if html_file.exists():
                # 质量门禁：检查是否违规引用 raw_images
                content = html_file.read_text(encoding="utf-8")
                if "raw_images" in content:
                    raise ValueError(f"🚨 质量门禁拦截：{html_file.name} 包含未经脱敏的 raw_images 引用！")
                
                page = browser.new_page(viewport={"width": 1080, "height": 1440})
                page.goto(f"file://{html_file}")
                page.wait_for_timeout(1000)
                page.screenshot(path=str(png_file))
                print(f"✅ [{num}/4] 渲染完成: {png_file.name} ({os.path.getsize(png_file)} 字节)")
        browser.close()

    print("🎉 全部 4 张 3:4 合规图文卡片已生成完毕！")
    return [
        output_dir / "card_01_cover.png",
        output_dir / "card_02_detail_a.png",
        output_dir / "card_03_detail_b.png",
        output_dir / "card_04_sop_compliance.png"
    ]

if __name__ == "__main__":
    generate_all_cards()
