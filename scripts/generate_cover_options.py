#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成 4 套抖音高转化率、高美学封面候选 (Douyin High-CTR Cover Generator)
"""

import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

BRAIN_DIR = Path("/Users/jackiecruise/.gemini/antigravity-ide/brain/0ef40ef1-b0be-4576-9a74-a20cfc2f8826")
PROJ_OUTPUTS = Path("/Users/workspace/ai_short_company/ai-short-drama/projects/handdraw_marriage_squeeze/outputs")
PROJ_FRAMES = Path("/Users/workspace/ai_short_company/ai-short-drama/projects/handdraw_marriage_squeeze/work/video_frames")

FONT_HEITI_BOLD = "/System/Library/Fonts/STHeiti Medium.ttc"
FONT_HEITI_LIGHT = "/System/Library/Fonts/STHeiti Light.ttc"

def get_font(path: str, size: int):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()

def draw_text_with_shadow(draw, pos, text, font, fill_color, shadow_color=(0, 0, 0, 180), offset=(4, 4)):
    x, y = pos
    draw.text((x + offset[0], y + offset[1]), text, font=font, fill=shadow_color)
    draw.text((x, y), text, font=font, fill=fill_color)

def generate_cover_option_1():
    """
    选项 1：【社会学隐喻款 · 阶梯模型死局】（视觉与概念顶峰）
    底图：AI 生成的阶梯错配图（A女在顶，D男在底，中间拼图断裂）
    在右上黑底负空间与居中区域排入黑金/白高反差大字
    """
    bg_path = BRAIN_DIR / "marriage_cover_concept_ai_1792546082758.jpg"
    im = Image.open(bg_path).convert("RGBA").resize((1080, 1920))
    
    overlay = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    font_badge = get_font(FONT_HEITI_BOLD, 36)
    font_main = get_font(FONT_HEITI_BOLD, 88)
    font_sub = get_font(FONT_HEITI_BOLD, 46)
    font_tag = get_font(FONT_HEITI_LIGHT, 34)
    
    # 顶部主题小标（安全区内，Y=220）
    badge_text = "社会学深度剖析 · 婚姻梯队模型"
    draw.rounded_rectangle([(480, 240), (1010, 310)], radius=12, fill=(255, 215, 0, 35), outline=(255, 215, 0, 180), width=2)
    draw.text((505, 252), badge_text, font=get_font(FONT_HEITI_BOLD, 32), fill=(255, 220, 100, 255))
    
    # 主标题（位于右侧黑色留白区，Y=350~560，与左侧楼梯形成完美平衡）
    title_line1 = "为什么越优秀"
    title_line2 = "越结不起婚？"
    draw_text_with_shadow(draw, (480, 340), title_line1, font_main, fill_color=(255, 255, 255, 255), shadow_color=(0, 0, 0, 230), offset=(4, 5))
    draw_text_with_shadow(draw, (480, 450), title_line2, font_main, fill_color=(255, 204, 0, 255), shadow_color=(0, 0, 0, 230), offset=(4, 5))
    
    # 副标题与悬念提炼（居中黄金安全带）
    sub_box = [(480, 580), (1010, 680)]
    draw.rounded_rectangle(sub_box, radius=8, fill=(20, 20, 20, 220), outline=(80, 80, 80, 180), width=1)
    draw.text((505, 595), "底层数学死局：", font=font_sub, fill=(230, 70, 70, 255))
    draw.text((505, 638), "A女剩顶峰 · D男挤谷底", font=get_font(FONT_HEITI_BOLD, 34), fill=(220, 220, 220, 255))

    # 合并图层
    final = Image.alpha_composite(im, overlay).convert("RGB")
    out_file = PROJ_OUTPUTS / "cover_option_1_gradient_metaphor.jpg"
    final.save(out_file, quality=95)
    print(f"✅ 生成封面选项 1: {out_file}")
    return out_file

def generate_cover_option_2():
    """
    选项 2：【深度特稿手绘款 · 结婚暴跌与相亲角】
    底图：极简暖纸质感手绘（断崖暴跌折线 + 相亲角简历伞 + 精英女性与男青年剪影）
    顶部强化主标，突出“结婚登记创新低”的时代警钟
    """
    bg_path = BRAIN_DIR / "marriage_cover_handdraw_pro_1792546131144.jpg"
    im = Image.open(bg_path).convert("RGBA").resize((1080, 1920))
    
    overlay = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    font_title = get_font(FONT_HEITI_BOLD, 92)
    font_sub = get_font(FONT_HEITI_BOLD, 44)
    font_small = get_font(FONT_HEITI_BOLD, 36)
    
    # 顶部加醒目深蓝/黑大字标题（避开极顶，Y=180~360）
    draw.rounded_rectangle([(80, 140), (1000, 210)], radius=8, fill=(225, 45, 45, 230))
    draw.text((120, 150), "民政局登记连年暴跌 · 底层逻辑", font=font_small, fill=(255, 255, 255, 255))
    
    draw.text((80, 230), "不是年轻人太挑剔", font=font_title, fill=(20, 24, 35, 255))
    draw.text((80, 340), "是数学机制卡死了", font=font_title, fill=(215, 35, 35, 255))
    
    # 中间加一层柔和说明胶囊
    draw.rounded_rectangle([(80, 460), (750, 520)], radius=6, fill=(30, 40, 60, 200))
    draw.text((100, 472), "相亲角A女愁嫁 vs 县城D男难娶", font=get_font(FONT_HEITI_BOLD, 34), fill=(255, 255, 255, 255))

    final = Image.alpha_composite(im, overlay).convert("RGB")
    out_file = PROJ_OUTPUTS / "cover_option_2_editorial_handdraw.jpg"
    final.save(out_file, quality=95)
    print(f"✅ 生成封面选项 2: {out_file}")
    return out_file

def generate_cover_option_3():
    """
    选项 3：【原片图解手绘强化款 · 真实手绘连贯风】
    底图：视频中 Act 3 的错配手绘原帧 (frame_act3.jpg)
    叠加深色高斯模糊渐变蒙版 + 居中强化文字排版
    """
    frame_path = PROJ_FRAMES / "frame_act3.jpg"
    im = Image.open(frame_path).convert("RGBA").resize((1080, 1920))
    
    # 创建上下渐变暗角蒙版，让画面更具电影感
    mask = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    d_mask = ImageDraw.Draw(mask)
    
    # 顶部与底部加深渐变
    for y in range(400):
        alpha = int(220 * (1 - y / 400))
        d_mask.line([(0, y), (1080, y)], fill=(15, 18, 26, alpha))
    for y in range(1400, 1920):
        alpha = int(240 * ((y - 1400) / 520))
        d_mask.line([(0, y), (1080, y)], fill=(15, 18, 26, alpha))
        
    im = Image.alpha_composite(im, mask)
    
    # 叠加标题排版
    overlay = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    font_main = get_font(FONT_HEITI_BOLD, 92)
    font_sub = get_font(FONT_HEITI_BOLD, 42)
    
    # 顶部标题区
    draw.rounded_rectangle([(100, 180), (450, 245)], radius=8, fill=(240, 70, 70, 240))
    draw.text((120, 192), "深度机制揭秘", font=get_font(FONT_HEITI_BOLD, 36), fill=(255, 255, 255, 255))
    
    draw_text_with_shadow(draw, (100, 270), "婚姻梯队错配", font_main, fill_color=(255, 255, 255, 255), shadow_color=(0, 0, 0, 200), offset=(3, 4))
    draw_text_with_shadow(draw, (100, 380), "为什么越优秀越单身？", font=get_font(FONT_HEITI_BOLD, 68), fill_color=(255, 210, 50, 255), shadow_color=(0, 0, 0, 200), offset=(3, 4))

    # 底部说明胶囊
    draw.rounded_rectangle([(100, 1580), (980, 1680)], radius=16, fill=(20, 25, 35, 230), outline=(255, 215, 0, 150), width=2)
    draw.text((140, 1600), "A男娶B女，B男娶C女，C男娶D女", font=font_sub, fill=(240, 240, 240, 255))
    draw.text((140, 1642), "传统机制崩溃后，两端如何破局？", font=get_font(FONT_HEITI_LIGHT, 32), fill=(255, 200, 80, 255))

    final = Image.alpha_composite(im, overlay).convert("RGB")
    out_file = PROJ_OUTPUTS / "cover_option_3_video_frame_pro.jpg"
    final.save(out_file, quality=95)
    print(f"✅ 生成封面选项 3: {out_file}")
    return out_file

def generate_cover_option_4():
    """
    选项 4：【极简大字报 · 爆款痛点直击款】
    黑曜石微质感暗色背景 + 黄金分割区超大视觉冲击文字，适合作为纯文字直击型封面
    """
    im = Image.new("RGB", (1080, 1920), (14, 16, 22))
    draw = ImageDraw.Draw(im)
    
    # 绘制高雅金色边框
    draw.rectangle([(50, 50), (1030, 1870)], outline=(60, 65, 80), width=3)
    draw.rectangle([(65, 65), (1015, 1855)], outline=(218, 165, 32, 100), width=1)
    
    font_hero = get_font(FONT_HEITI_BOLD, 106)
    font_mid = get_font(FONT_HEITI_BOLD, 52)
    font_sm = get_font(FONT_HEITI_BOLD, 36)
    
    # 顶部小标
    draw.text((120, 480), "—— 社会学与经济学模型 ——", font=font_sm, fill=(160, 165, 180))
    
    # 核心大字（黄金居中区）
    draw.text((120, 580), "为什么现在结婚", font=font_hero, fill=(255, 255, 255))
    draw.text((120, 710), "人数断崖暴跌？", font=font_hero, fill=(255, 204, 0))
    
    # 分隔金线
    draw.line([(120, 870), (960, 870)], fill=(218, 165, 32), width=3)
    
    # 悬念副标
    draw.text((120, 930), "真不是年轻人挑剔自私，", font=font_mid, fill=(230, 230, 230))
    draw.text((120, 1010), "而是底层数学机制卡死了。", font=font_mid, fill=(255, 90, 90))
    
    # 关键梯队胶囊
    tags = ["A女剩顶峰", "D男沉谷底", "试错成本剧增", "理性避险"]
    cur_x = 120
    for t in tags:
        draw.rounded_rectangle([(cur_x, 1140), (cur_x + 180, 1205)], radius=8, fill=(35, 40, 55), outline=(90, 100, 130), width=1)
        draw.text((cur_x + 15, 1158), t, font=get_font(FONT_HEITI_BOLD, 28), fill=(255, 220, 120))
        cur_x += 205

    out_file = PROJ_OUTPUTS / "cover_option_4_bold_typography.jpg"
    im.save(out_file, quality=95)
    print(f"✅ 生成封面选项 4: {out_file}")
    return out_file

if __name__ == "__main__":
    generate_cover_option_1()
    generate_cover_option_2()
    generate_cover_option_3()
    generate_cover_option_4()
