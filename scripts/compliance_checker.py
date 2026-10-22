"""
小红书/全平台发布与防限流质量门禁检测器 (Compliance Quality Gate)

针对小红书《笔记存在推广其他平台的内容》限流处罚规则进行硬性拦截：
1. 严禁展示其他平台界面信息 (店面截图、订单截图、App UI等)；
2. 严禁敏感导流词与第三方平台名称明文；
3. 强制校验官方【笔记含AI合成内容】配置；
4. 图像脱敏：剔除第三方平台特征，仅保留纯作品效果本身。
"""

import re
from pathlib import Path
from PIL import Image, ImageFilter

# 违禁平台与导流词汇映射表 (敏感词 -> 合规中性词)
PLATFORM_WORDS_MAP = {
    "闲鱼": "二手闲置平台",
    "淘宝": "电商平台",
    "天猫": "线上品牌商城",
    "拼多多": "电商供应链",
    "1688": "货源供应链",
    "微信": "私域社群",
    "微信号": "创作者联系方式",
    "公众号": "深度长文社区",
    "朋友圈": "创作者动态",
    "小鹅通": "知识服务平台",
    "抖音": "短视频平台",
    "快手": "短视频社区",
    "加v": "建立连接",
    "加微": "建立连接",
    "vx": "私信",
    "私聊": "留言互动",
    "引流": "客户连接",
    "导流": "商业交付",
    "外链": "站外资源",
    "买家秀": "用户实拍",
    "订单截图": "交易实录",
    "店铺截图": "案例实录",
}

def sanitize_text(text: str) -> tuple[str, list[str]]:
    """扫描并自动替换文本中的违禁第三方平台词汇与导流词"""
    replaced_log = []
    sanitized = text
    for word, replacement in PLATFORM_WORDS_MAP.items():
        if word in sanitized:
            sanitized = sanitized.replace(word, replacement)
            replaced_log.append(f"敏感词替换: [{word}] -> [{replacement}]")
    return sanitized, replaced_log

def check_text_compliance(text: str) -> tuple[bool, list[str]]:
    """严格检查文本是否依然包含违禁平台或导流词"""
    violations = []
    for word in PLATFORM_WORDS_MAP.keys():
        if word in text:
            violations.append(f"发现违禁平台/导流词: '{word}'")
    is_passed = len(violations) == 0
    return is_passed, violations

def smart_crop_and_fit(im: Image.Image, target_w: int, target_h: int, top_anchor: float = 0.0) -> Image.Image:
    """
    等比智能裁切适配 (Aspect-Preserving Smart Fit) - 防拉伸与防断头核心工具函数:
    - 绝不允许各向异性拉伸 (宽高比失真度严格为 0%)
    - 顶部锚点对齐 (top_anchor=0.0 为贴顶优先保留头部/发顶，避免断头)
    """
    w, h = im.size
    target_ratio = target_w / target_h
    src_ratio = w / h

    if abs(src_ratio - target_ratio) < 0.01:
        return im.resize((target_w, target_h), Image.Resampling.LANCZOS)

    if src_ratio > target_ratio:
        # 原图偏宽：按高度缩放到 target_h，水平居中裁切左右
        new_w = int(h * target_ratio)
        left = (w - new_w) // 2
        crop_box = (left, 0, left + new_w, h)
    else:
        # 原图偏高/偏瘦：按宽度缩放到 target_w，垂直方向以 top_anchor 优先保留上部头像
        new_h = int(w / target_ratio)
        top = int((h - new_h) * top_anchor)
        top = max(0, min(top, h - new_h))
        crop_box = (0, top, w, top + new_h)

    cropped = im.crop(crop_box)
    return cropped.resize((target_w, target_h), Image.Resampling.LANCZOS)

def audit_html_template(html_path: Path) -> tuple[bool, list[str]]:
    """审计 HTML 模板源码，严禁直接引用 raw_images、严禁包含违禁词、必须包含头部保护CSS"""
    if not html_path.exists():
        return False, [f"模板不存在: {html_path}"]
    content = html_path.read_text(encoding="utf-8")
    violations = []
    if "raw_images" in content:
        violations.append(f"🚨 严禁直接引用未经脱敏的 raw_images 资源: {html_path.name}")
    for word in ["闲鱼", "淘宝", "小鹅通", "拼多多", "微信", "抖音"]:
        if word in content:
            violations.append(f"⚠️ 模板包含第三方平台敏感词 [{word}]: {html_path.name}")
    # 头部完整度门禁检查：对于包含人物卡片的模板，应包含 object-position 定位防护
    if ".card-img" in content and "object-position" not in content:
        violations.append(f"⚠️ 模板卡片样式缺少 object-position 头部防断头保护: {html_path.name}")
    return len(violations) == 0, violations

def desensitize_case_image(input_path: Path, output_path: Path, crop_center_ratio: float = 0.8) -> Path:
    """
    对案例图像执行去平台UI指纹脱敏处理：
    - 居中安全裁切 (去除四周可能的 App 状态栏、底部导航栏、店铺边框、价格框)
    - 确保只保留作品主体本身
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(input_path) as img:
        w, h = img.size
        # 计算安全中心区域
        new_w = int(w * crop_center_ratio)
        new_h = int(h * crop_center_ratio)
        left = (w - new_w) // 2
        top = (h - new_h) // 2
        right = left + new_w
        bottom = top + new_h

        cropped = img.crop((left, top, right, bottom))
        # 转换并保存高质量去指纹图
        cropped.convert("RGB").save(output_path, "JPEG", quality=92)
        return output_path

def audit_publish_package(title: str, content: str, image_paths: list[Path], html_templates: list[Path] = None) -> dict:
    """
    发布前综合质量门禁总检
    返回门禁检查报告
    """
    report = {
        "passed": True,
        "title_length": len(title),
        "title_valid": len(title) <= 20,
        "text_violations": [],
        "image_count": len(image_paths),
        "image_checks": [],
        "template_violations": [],
        "actions_needed": []
    }

    # 1. 标题长度检验 (小红书标题限20字)
    if not report["title_valid"]:
        report["passed"] = False
        report["actions_needed"].append(f"标题长度超过20字 (当前{len(title)}字)，需截断")

    # 2. 文本违禁词扫描
    is_text_pass, text_viols = check_text_compliance(title + " " + content)
    if not is_text_pass:
        report["passed"] = False
        report["text_violations"] = text_viols
        report["actions_needed"].append("文本包含其他平台名称或导流词，需自动脱敏")

    # 3. 图像规格与存在性核验 (1080x1440 满幅核验)
    for p in image_paths:
        if not p.exists():
            report["passed"] = False
            report["actions_needed"].append(f"图片不存在: {p}")
        else:
            with Image.open(p) as im:
                w, h = im.size
                ratio_valid = abs(w / h - 0.75) < 0.02
                report["image_checks"].append({
                    "path": str(p.name),
                    "size": im.size,
                    "ratio": f"{w}:{h}",
                    "ratio_valid": ratio_valid
                })
                if not ratio_valid:
                    report["passed"] = False
                    report["actions_needed"].append(f"卡片 {p.name} 比例偏离 3:4 标准 (当前 {w}x{h})")

    # 4. HTML 模板源路径、脱敏合规与头部保护校验
    if html_templates:
        for t in html_templates:
            is_tmpl_pass, tmpl_viols = audit_html_template(t)
            if not is_tmpl_pass:
                report["passed"] = False
                report["template_violations"].extend(tmpl_viols)
                report["actions_needed"].extend(tmpl_viols)

    return report

if __name__ == "__main__":
    import json
    BASE_DIR = Path(__file__).resolve().parent.parent
    proj_dir = BASE_DIR / "projects/ai_beauty_monetization"
    note_file = proj_dir / "note_draft.json"
    
    if note_file.exists():
        with open(note_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        title = data.get("title", "")
        content = data.get("content", "")
        images = [proj_dir / "images" / f"card_0{i}_{name}.png" for i, name in [
            (1, "cover"), (2, "detail_a"), (3, "detail_b"), (4, "sop_compliance")
        ]]
        templates = [
            BASE_DIR / "scratch/x_to_xhs/magazine_cover_with_real_img.html",
            proj_dir / "images/card_02_detail_a.html",
            proj_dir / "images/card_03_detail_b.html",
            proj_dir / "images/card_04_sop_compliance.html",
        ]
        
        rep = audit_publish_package(title, content, images, templates)
        print("🛡️ [小红书防限流质量门禁检测报告]")
        print(f"门禁判定: {'✅ 100% 满分通过' if rep['passed'] else '❌ 拦截未通过'}")
        print(f"标题长度: {rep['title_length']}/20 (合规: {rep['title_valid']})")
        print(f"文本违规: {rep['text_violations']}")
        print(f"模板违规: {rep['template_violations']}")
        print(f"图片数量: {rep['image_count']} 张")
        for img in rep['image_checks']:
            print(f"  - {img['path']}: {img['size']}")
        if rep['actions_needed']:
            print(f"待处理项: {rep['actions_needed']}")

