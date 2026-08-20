import json
import os

TEMPLATES = [
    {
        "dance_id": "DANCE_CAI_BAO_XIAO",
        "name": "白菜对我笑",
        "stats": {"views": "36亿", "difficulty": 1, "virality": 5},
        "duration_range": [15, 20],
        "bpm": "120-130",
        "tags": ["搞笑", "魔性", "手势舞", "全民挑战"],
        "recommendations": {
            "character": {"age": "AGE_YOUNG_ADULT", "body": ["BODY_SLIM", "BODY_ATHLETIC"]},
            "outfit": {"top": ["TOP_CROP_TOP", "TOP_OVERSIZED_TEE"], "bottom": ["BOTTOM_JEANS", "BOTTOM_MINISKIRT"], "shoes": ["SHOE_SNEAKERS"], "accessories": []},
            "scene": ["SCENE_GRAFFITI_WALL", "SCENE_PARK"],
            "music": ["MUSIC_POP", "MUSIC_CHINESE_POP"]
        },
        "timeline": [
            {"time": "0-3s", "name": "起手式", "action_prompt": "双手在胸前做抱白菜姿势，身体轻微左右摇摆", "expression": "微笑看镜头"},
            {"time": "3-8s", "name": "核心白菜摇", "action_prompt": "右手抬起挥手，左手做指白菜手势，身体随节奏左右摇摆幅度加大，原地踏步加轻微滑步，头部配合节奏点头", "expression": "微笑看镜头"},
            {"time": "8-13s", "name": "变奏加速", "action_prompt": "双手交替做白菜摇，加入360度慢转，滑步加踢腿", "expression": "惊讶眨眼"},
            {"time": "13-15s", "name": "收尾定格", "action_prompt": "双手比心，身体定格", "expression": "wink加微笑"}
        ],
        "camera_and_edit": {
            "camera": "FRONT_EYE_LEVEL, MEDIUM_SHOT",
            "edit_effects": ["SPEED_RAMP on Chorus"]
        }
    },
    {
        "dance_id": "DANCE_GET_ON_BUS",
        "name": "上车舞",
        "stats": {"views": "10亿", "difficulty": 2, "virality": 5},
        "duration_range": [12, 15],
        "bpm": "100-110",
        "tags": ["上车", "搞笑", "全民挑战", "明星同款"],
        "recommendations": {
            "character": {"age": "AGE_YOUNG_ADULT", "body": ["BODY_SLIM", "BODY_ATHLETIC"]},
            "outfit": {"top": ["TOP_OVERSIZED_TEE"], "bottom": ["BOTTOM_JEANS"]},
            "scene": ["SCENE_OUTDOOR_STREET", "SCENE_CORRIDOR"],
            "music": ["MUSIC_HIPHOP", "MUSIC_POP"]
        },
        "timeline": [
            {"time": "0-2s", "name": "等车", "action_prompt": "单手招手打车，身体前倾张望", "expression": "期待"},
            {"time": "2-5s", "name": "上车", "action_prompt": "双手做扶车门动作，身体模仿跨步上车，向前迈一步身体下沉", "expression": "期待"},
            {"time": "5-10s", "name": "坐稳开车", "action_prompt": "双手握方向盘，身体随节奏左右摇摆，头部点头", "expression": "享受与自信"},
            {"time": "10-12s", "name": "到站下车", "action_prompt": "单手拉扶手，身体前倾准备下车，最后双手摊开定格", "expression": "自然"}
        ]
    },
    {
        "dance_id": "DANCE_SUBJECT_3",
        "name": "科目三",
        "stats": {"views": "病毒传播", "difficulty": 3, "virality": 5},
        "duration_range": [15, 30],
        "bpm": "130-140",
        "tags": ["科目三", "崴脚步", "丝滑", "全球挑战", "抽象"],
        "recommendations": {
            "character": {"age": "AGE_YOUNG_ADULT"},
            "outfit": {"top": ["TOP_OVERSIZED_TEE"], "bottom": ["BOTTOM_JEANS", "WIDE_LEG"], "shoes": ["SHOE_SNEAKERS"]},
            "scene": ["SCENE_PARK", "SCENE_STAIRS", "SCENE_ROOFTOP"],
            "music": ["MUSIC_HIPHOP", "CHINESE_DJ"]
        },
        "timeline": [
            {"time": "0-3s", "name": "起手式", "action_prompt": "双脚并拢微蹲，双手胸前交叉", "expression": "神秘微笑"},
            {"time": "3-10s", "name": "崴脚步核心", "action_prompt": "脚踝内旋外滑之字步，上半身平稳手臂自然摆动，速度加快", "expression": "神秘微笑"},
            {"time": "10-18s", "name": "丝滑手部", "action_prompt": "双手做波浪动作，头部跟随，扭胯 Hip Roll", "expression": "神秘微笑"},
            {"time": "18-25s", "name": "全身波浪", "action_prompt": "从头到脚 Body Wave，180度转身，崴脚步加速", "expression": "神秘微笑"},
            {"time": "25-30s", "name": "收尾", "action_prompt": "双手展开定格", "expression": "自信微笑"}
        ]
    },
    {
        "dance_id": "DANCE_PENGUIN",
        "name": "企鹅舞",
        "stats": {"views": "千万级", "difficulty": 1, "virality": 4},
        "duration_range": [10, 15],
        "bpm": "110-120",
        "tags": ["企鹅", "库里之歌", "呆萌", "简单好学", "健身"],
        "recommendations": {
            "outfit": {"top": ["TOP_HOODIE"], "bottom": ["BOTTOM_LEGGINGS"], "shoes": ["SHOE_CANVAS"]},
            "scene": ["SCENE_SOLID_COLOR", "SCENE_PARK_SNOW"]
        },
        "timeline": [
            {"time": "0-2s", "name": "企鹅亮相", "action_prompt": "双臂紧贴身体两侧，双脚并拢，身体微前倾", "expression": "呆萌"},
            {"time": "2-7s", "name": "企鹅摇摆", "action_prompt": "身体髋部左右摇摆，小碎步左右移动，手臂夹紧", "expression": "呆萌"},
            {"time": "7-12s", "name": "企鹅加速", "action_prompt": "摇摆幅度加大，360度转身，手臂偶尔打开再合上", "expression": "开心大笑"},
            {"time": "12-15s", "name": "定格", "action_prompt": "恢复企鹅姿势，双手比V", "expression": "wink"}
        ]
    },
    {
        "dance_id": "DANCE_LEMONADE_AESPA",
        "name": "Lemonade",
        "stats": {"views": "千万级", "difficulty": 3, "virality": 4},
        "duration_range": [15, 20],
        "bpm": "120-125",
        "tags": ["aespa", "Kpop", "挤柠檬", "女团舞", "酷飒"],
        "recommendations": {
            "outfit": {"top": ["TOP_CROP_TOP"], "bottom": ["BOTTOM_LEGGINGS"], "shoes": ["SHOE_HEELS", "SHOE_SNEAKERS"], "accessories": ["ACCESSORY_NECKLACE"]},
            "scene": ["SCENE_DANCE_STUDIO", "SCENE_PARKING_LOT"],
            "music": ["MUSIC_KPOP"]
        },
        "timeline": [
            {"time": "0-3s", "name": "起手", "action_prompt": "双手头顶做柠檬形状，微蹲", "expression": "冷酷"},
            {"time": "3-8s", "name": "挤柠檬", "action_prompt": "双手向下挤压，Body Wave，左右滑步，头部侧倾", "expression": "冷酷"},
            {"time": "8-13s", "name": "加速段", "action_prompt": "挤柠檬加速，转身，手臂波浪", "expression": "自信微笑"},
            {"time": "13-15s", "name": "收尾", "action_prompt": "双手放下定格", "expression": "酷飒眼神"}
        ]
    },
    {
        "dance_id": "DANCE_JUMP_BLACKPINK",
        "name": "JUMP",
        "stats": {"views": "破亿", "difficulty": 3, "virality": 5},
        "duration_range": [15, 20],
        "bpm": "125-130",
        "tags": ["BLACKPINK", "JUMP", "Kpop", "女团", "墨色"],
        "recommendations": {
            "outfit": {"top": ["TOP_TIGHT_TEE"], "bottom": ["BOTTOM_JEANS"], "shoes": ["SHOE_SNEAKERS"]},
            "scene": ["SCENE_PARKING_LOT", "SCENE_DANCE_STUDIO"]
        },
        "timeline": [
            {"time": "0-3s", "name": "预备", "action_prompt": "双脚并拢微蹲，双手下垂", "expression": "专注"},
            {"time": "3-8s", "name": "跳跃段", "action_prompt": "双脚跳起，空中手臂画圈，落地缓冲身体摇摆", "expression": "专注"},
            {"time": "8-13s", "name": "手臂波浪", "action_prompt": "双手从指尖到肩膀做Wave，身体左右摇摆，原地踏步", "expression": "专注"},
            {"time": "13-15s", "name": "收尾", "action_prompt": "双手交叉胸前定格", "expression": "酷飒"}
        ]
    },
    {
        "dance_id": "DANCE_ANGLE_AESPA",
        "name": "Angel",
        "stats": {"views": "千万级", "difficulty": 2, "virality": 4},
        "duration_range": [12, 15],
        "bpm": "115-120",
        "tags": ["aespa", "Angel", "天使", "梦幻", "女团"],
        "recommendations": {
            "outfit": {"top": ["TOP_SHIRT"], "bottom": ["BOTTOM_MAXI_SKIRT"], "shoes": ["SHOE_HEELS"]},
            "scene": ["SCENE_ROOFTOP", "SCENE_PARK"]
        },
        "timeline": [
            {"time": "0-2s", "name": "天使降临", "action_prompt": "双手背后做收翼状，微蹲", "expression": "神秘"},
            {"time": "2-7s", "name": "展翅", "action_prompt": "双臂向两侧展开，慢慢站起，头部仰望，向前迈一步", "expression": "神秘"},
            {"time": "7-11s", "name": "旋转", "action_prompt": "360度旋转，手臂保持展开", "expression": "微笑"},
            {"time": "11-13s", "name": "收尾", "action_prompt": "双手放胸前定格", "expression": "温柔"}
        ]
    },
    {
        "dance_id": "DANCE_THAI_SWAY",
        "name": "二摆/泰国摇",
        "stats": {"views": "过亿", "difficulty": 2, "virality": 5},
        "duration_range": [10, 15],
        "bpm": "100-110",
        "tags": ["泰国摇", "抽象", "灵魂出窍", "土嗨", "魔性"],
        "recommendations": {
            "outfit": {"top": ["TOP_OVERSIZED_TEE"], "bottom": ["BOTTOM_SHORTS"]},
            "scene": ["SCENE_BEACH", "SCENE_PARK"]
        },
        "timeline": [
            {"time": "0-2s", "name": "起手", "action_prompt": "双手自然下垂，微蹲", "expression": "放空"},
            {"time": "2-8s", "name": "灵魂摇摆", "action_prompt": "身体大幅左右摇摆，手臂放松摆动，头部晃动，原地小碎步", "expression": "放空"},
            {"time": "8-12s", "name": "加速", "action_prompt": "摇摆幅度加大，转身", "expression": "迷离陶醉"},
            {"time": "12-15s", "name": "定格", "action_prompt": "突然静止", "expression": "正常微反差"}
        ]
    },
    {
        "dance_id": "DANCE_QING_TIAN_DA_LAO_YE",
        "name": "青天大老爷",
        "stats": {"views": "过亿", "difficulty": 1, "virality": 4},
        "duration_range": [8, 12],
        "bpm": "100-110",
        "tags": ["青天大老爷", "手势舞", "萌", "古风", "搞笑"],
        "recommendations": {
            "outfit": {"top": ["TOP_OVERSIZED_TEE"], "bottom": ["BOTTOM_JEANS"]},
            "scene": ["SCENE_INDOOR_BEDROOM", "SCENE_CORRIDOR"]
        },
        "timeline": [
            {"time": "0-2s", "name": "拱手", "action_prompt": "双手合十拱手姿势，微鞠躬", "expression": "严肃"},
            {"time": "2-6s", "name": "指天", "action_prompt": "右手食指指天，左手拱手，身体左右摇摆", "expression": "认真"},
            {"time": "6-9s", "name": "变脸", "action_prompt": "双手比心，小跳", "expression": "萌"},
            {"time": "9-12s", "name": "收尾", "action_prompt": "恢复拱手姿势", "expression": "wink"}
        ]
    },
    {
        "dance_id": "DANCE_REVENGE_SHAKE",
        "name": "复仇摇",
        "stats": {"views": "千万级", "difficulty": 2, "virality": 4},
        "duration_range": [12, 15],
        "bpm": "120-130",
        "tags": ["复仇摇", "力量感", "零基础", "男团舞", "酷飒"],
        "recommendations": {
            "outfit": {"top": ["TOP_HOODIE"], "bottom": ["BOTTOM_SPORT_PANTS"]},
            "scene": ["SCENE_PARKING_LOT", "SCENE_STAIRS"]
        },
        "timeline": [
            {"time": "0-2s", "name": "起手", "action_prompt": "双手胸前交叉，微蹲", "expression": "愤怒坚定"},
            {"time": "2-7s", "name": "交叉挥动", "action_prompt": "双手交替向两侧挥动，身体左右摇摆，原地滑步", "expression": "坚定"},
            {"time": "7-11s", "name": "转身", "action_prompt": "360度旋转，手臂展开收回", "expression": "自信微笑"},
            {"time": "11-13s", "name": "收尾", "action_prompt": "双手叉腰定格", "expression": "酷飒"}
        ]
    },
    {
        "dance_id": "DANCE_HIME_ME_SHAKE",
        "name": "姬芽摇",
        "stats": {"views": "千万级", "difficulty": 1, "virality": 4},
        "duration_range": [10, 12],
        "bpm": "130-140",
        "tags": ["姬芽摇", "萌系", "甜妹", "可爱", "手势舞"],
        "recommendations": {
            "outfit": {"top": ["TOP_CROP_TOP"], "bottom": ["BOTTOM_MINISKIRT"]},
            "scene": ["SCENE_PARK", "SCENE_INDOOR_BEDROOM"]
        },
        "timeline": [
            {"time": "0-2s", "name": "亮相", "action_prompt": "双手脸颊旁做花朵状，微蹲", "expression": "甜美微笑"},
            {"time": "2-6s", "name": "核心摇摆", "action_prompt": "双手胸前交替开花，身体快速左右摇摆，小碎步", "expression": "甜美微笑"},
            {"time": "6-9s", "name": "变奏", "action_prompt": "转身，双手做蝴蝶飞", "expression": "开心大笑"},
            {"time": "9-12s", "name": "收尾", "action_prompt": "双手比心定格", "expression": "wink甜笑"}
        ]
    },
    {
        "dance_id": "DANCE_CURRY_SONG",
        "name": "库里之歌",
        "stats": {"views": "过亿", "difficulty": 1, "virality": 4},
        "duration_range": [10, 15],
        "bpm": "110-120",
        "tags": ["库里之歌", "企鹅", "投篮", "呆萌", "健身"],
        "recommendations": {
            "outfit": {"top": ["TOP_HOODIE"], "bottom": ["BOTTOM_LEGGINGS"]},
            "scene": ["SCENE_SOLID_COLOR", "SCENE_PARK"]
        },
        "timeline": [
            {"time": "0-2s", "name": "企鹅亮相", "action_prompt": "双臂夹紧身体，双脚并拢", "expression": "呆萌"},
            {"time": "2-7s", "name": "企鹅摇摆加投篮", "action_prompt": "身体左右企鹅步摇摆，右手做投篮动作", "expression": "认真搞笑"},
            {"time": "7-11s", "name": "加速摇摆", "action_prompt": "摇摆加大，转身，双手投篮", "expression": "开心"},
            {"time": "11-15s", "name": "收尾", "action_prompt": "恢复企鹅姿势，双手比V", "expression": "wink"}
        ]
    }
]

def main():
    target_dir = os.path.join(os.path.dirname(__file__), "assets", "dance", "07_templates")
    os.makedirs(target_dir, exist_ok=True)
    
    for t in TEMPLATES:
        filename = f"{t['dance_id']}.json"
        filepath = os.path.join(target_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(t, f, ensure_ascii=False, indent=2)
        print(f"Generated {filepath}")

if __name__ == "__main__":
    main()
