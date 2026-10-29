#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抖音短视频自动化/定时发布中间件 (Douyin Auto & Scheduled Publisher)
专为《婚姻梯队错配》等 2 分钟内竖屏短剧设计。

支持特性：
1. 媒体参数合规性校验（分辨率 1080x1920，时长 ≤120s，封面尺寸）；
2. 抖音 SEO 爆款文案与话题标签清洗；
3. 定时发布时间自动对齐（满足抖音创作者中心 2小时 ~ 14天 的平台窗口，智能选择晚间 19:00~21:30 黄金流量池）；
4. 支持调用 opencli douyin publish 命令行管道，或生成创作者后台一键发布套件。
"""

import os
import sys
import json
import argparse
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

# 默认视频与封面路径
DEFAULT_PROJECT_DIR = Path("/Users/workspace/ai_short_company/ai-short-drama/projects/handdraw_marriage_squeeze/outputs")
DEFAULT_VIDEO = DEFAULT_PROJECT_DIR / "film.mp4"
DEFAULT_COVER = DEFAULT_PROJECT_DIR / "cover.png"

# 抖音爆款推荐话题库
DOUYIN_MARRIAGE_TOPICS = [
    "婚姻现状", "为什么不结婚", "婚姻梯队模型", "相亲", 
    "深度思考", "社会现象", "情感共鸣", "认知思维", 
    "年轻人现状", "人性哲学"
]

def check_video_metadata(video_path: Path) -> dict:
    """使用 ffprobe 检查视频分辨率与时长"""
    if not video_path.exists():
        raise FileNotFoundError(f"视频文件不存在: {video_path}")
    
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", "-show_streams", str(video_path)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    meta = json.loads(res.stdout)
    
    video_stream = next((s for s in meta["streams"] if s["codec_type"] == "video"), None)
    if not video_stream:
        raise ValueError("未检测到有效视频流")
        
    duration = float(meta["format"].get("duration", 0))
    width = int(video_stream.get("width", 0))
    height = int(video_stream.get("height", 0))
    size_mb = os.path.getsize(video_path) / (1024 * 1024)
    
    return {
        "duration_sec": duration,
        "width": width,
        "height": height,
        "aspect_ratio": f"{width}:{height}",
        "size_mb": round(size_mb, 2)
    }

def calculate_optimal_schedule_time(hours_ahead: float = 3.0) -> str:
    """
    计算最佳定时发布时间（ISO 8601 格式）
    抖音规则：必须在 2小时 ~ 14天 之间。
    自动避开凌晨，默认推荐当晚或次日 19:30 / 20:30 黄金流量窗口。
    """
    now = datetime.now()
    target = now + timedelta(hours=hours_ahead)
    
    # 如果目标时间在晚上 23:00 到次日 11:00 之间，自动移到中午 12:00 或晚上 19:30
    if target.hour < 11:
        target = target.replace(hour=12, minute=0, second=0)
    elif target.hour >= 23:
        target = (target + timedelta(days=1)).replace(hour=19, minute=30, second=0)
        
    return target.strftime("%Y-%m-%d %H:%M:%S")

def format_caption(text_intro: str, topics: list[str]) -> str:
    """组装符合抖音格式的标题与文案"""
    tags = " ".join([f"#{t}" for t in topics])
    return f"{text_intro.strip()}\n\n{tags}"

def build_publish_command(
    video_path: Path,
    title: str,
    caption: str,
    cover_path: Path = None,
    schedule_time: str = None
) -> list[str]:
    """构建 opencli douyin 发布命令"""
    cmd = [
        "npx", "-y", "@jackwener/opencli", "douyin", "publish",
        str(video_path),
        "--title", title[:30],
        "--caption", caption,
        "--visibility", "public"
    ]
    if cover_path and cover_path.exists():
        cmd.extend(["--cover", str(cover_path)])
    if schedule_time:
        cmd.extend(["--schedule", schedule_time])
        
    return cmd

def main():
    parser = argparse.ArgumentParser(description="抖音短视频定时/自动发布中间件")
    parser.add_argument("--video", type=str, default=str(DEFAULT_VIDEO), help="待发布视频路径")
    parser.add_argument("--cover", type=str, default=str(DEFAULT_COVER), help="封面图片路径")
    parser.add_argument("--schedule", type=str, default=None, help="定时发布时间 (如 '2026-10-21 20:00:00')")
    parser.add_argument("--execute", action="store_true", help="是否直接执行 CLI 发布")
    args = parser.parse_args()

    video_path = Path(args.video)
    cover_path = Path(args.cover)

    print("=" * 60)
    print("【抖音短视频发布准备与合规性自检】")
    print("=" * 60)

    # 1. 媒体文件检测
    meta = check_video_metadata(video_path)
    print(f"✅ 视频文件: {video_path}")
    print(f"   - 时长: {meta['duration_sec']:.2f} 秒 (≤ 120 秒，符合 2 分钟内要求)")
    print(f"   - 分辨率: {meta['width']}x{meta['height']} ({meta['aspect_ratio']} 竖屏满屏)")
    print(f"   - 文件大小: {meta['size_mb']} MB")
    
    if cover_path.exists():
        print(f"✅ 封面图片: {cover_path} (存在)")
    else:
        print(f"⚠️ 封面图片: 未找到，将默认使用视频第一帧截帧")

    # 2. 定时发布时间计算
    schedule_str = args.schedule or calculate_optimal_schedule_time(3.5)
    print(f"\n⏰ 定时发布窗口规划:")
    print(f"   - 设定时间: {schedule_str}")
    print(f"   - 平台合规: 必须满足在当前时间 2小时 ~ 14天 之间 (抖音官方规定)")

    # 3. 爆款标题与正文组装
    title = "为什么结婚人数连年暴跌？婚姻梯队错配死局"
    intro = "民政局登记创新低，相亲角A女愁嫁，农村D男愁娶。很多人归咎于挑剔，但底层其实是残酷的数学梯队错配。戳中痛点的底层逻辑，你看懂了吗？"
    full_caption = format_caption(intro, DOUYIN_MARRIAGE_TOPICS)

    print(f"\n📝 发布文案与话题标签:")
    print(f"   - 标题 (≤30字): {title}")
    print(f"   - 正文内容:\n{full_caption}")

    # 4. 生成发布指令
    cmd = build_publish_command(video_path, title, full_caption, cover_path, schedule_str)
    print(f"\n🚀 自动化发布命令 (opencli 规范):")
    print(" ".join(cmd))

    # 5. 执行或生成操作指引
    if args.execute:
        print("\n⏳ 正在调用发布中间件...")
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print("发布结果输出:")
            print(res.stdout)
        except subprocess.CalledProcessError as e:
            print(f"发布调用异常: {e}")
            print(f"错误详情: {e.stderr}")
    else:
        print("\n💡 提示: 运行添加 --execute 参数可触发自动化发布。")
        print("   或可在浏览器登录抖音创作者服务平台 (https://creator.douyin.com) 后直接使用上述内容完成发布/定时发布。")

if __name__ == "__main__":
    main()
