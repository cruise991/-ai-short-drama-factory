"""
Unified Skills Hub & Content Industrialization Engine (统一技能注册与内容工业化中枢)
Centralized registry and execution pipeline for:
  1. Agent Reach (Multi-platform web research)
  2. OpenCLI (Automated web operation & scraping)
  3. NotebookLM Engine (Knowledge systematization & concept matrix)
  4. Baoyu Structuring (Gestalt narrative architecture & completion guardrail)
  5. Humanizer-zh (De-AI flavor, colloquial voice & unconscious emotion)
"""
import os
import sys
import json
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

BASE_DIR = Path(__file__).resolve().parent.parent

@dataclass
class SkillDescriptor:
    id: str
    name: str
    category: str # 'research' | 'automation' | 'knowledge' | 'structuring' | 'humanize'
    skill_path: str
    description: str
    is_active: bool = True
    config: Dict[str, Any] = field(default_factory=dict)

class SkillsRegistry:
    """Central registry and executor for all enterprise skills."""
    _skills: Dict[str, SkillDescriptor] = {}

    @classmethod
    def register(cls, descriptor: SkillDescriptor):
        cls._skills[descriptor.id] = descriptor

    @classmethod
    def get(cls, skill_id: str) -> Optional[SkillDescriptor]:
        return cls._skills.get(skill_id)

    @classmethod
    def list_all(cls) -> List[SkillDescriptor]:
        return list(cls._skills.values())

    @classmethod
    def auto_discover(cls):
        """Discovers and binds the standard 5-tier industrial skills."""
        # 1. Agent Reach
        agent_reach_path = BASE_DIR / "skills" / "agent-reach"
        cls.register(SkillDescriptor(
            id="agent-reach",
            name="Agent Reach (全网多平台调研与痛点嗅探)",
            category="research",
            skill_path=str(agent_reach_path),
            description="覆盖小红书、抖音、B站、知乎、X、V2EX等平台，搜索真实受众痛点与高赞金句",
            is_active=agent_reach_path.exists()
        ))

        # 2. OpenCLI
        cls.register(SkillDescriptor(
            id="opencli",
            name="OpenCLI (网页与自动化操作执行器)",
            category="automation",
            skill_path="",
            description="驱动浏览器进行无头抓取、表单提交与自动化数据采集中转",
            is_active=True
        ))

        # 3. NotebookLM Engine
        cls.register(SkillDescriptor(
            id="notebooklm",
            name="NotebookLM Content Brain (素材系统化与概念矩阵)",
            category="knowledge",
            skill_path="",
            description="将多源文献、长研报、视听转录稿系统化归纳，提炼权威机制与硬核论据",
            is_active=True
        ))

        # 4. Baoyu Structuring Skill
        cls.register(SkillDescriptor(
            id="baoyu",
            name="Baoyu Narrative Structuring (视听叙事架构与质量底盘)",
            category="structuring",
            skill_path="",
            description="压实 60s 视听骨架：黄金3秒钩子 ➔ 认知颠覆 ➔ 机制揭秘 ➔ 情绪峰值 ➔ 行动抓手",
            is_active=True
        ))

        # 5. Humanizer-zh (qu-ai-wei & nuwa)
        qu_ai_wei_path = Path("/Users/workspace/ai_short_company/.agents/skills/qu_ai_wei")
        cls.register(SkillDescriptor(
            id="humanizer-zh",
            name="Humanizer-zh (去 AI 味与拟真口语洗稿)",
            category="humanize",
            skill_path=str(qu_ai_wei_path),
            description="抹杀机械总结腔与教条说辞，注入生活化口语、微情绪波动与断句气口",
            is_active=True
        ))

# Initialize registry
SkillsRegistry.auto_discover()


class ContentPipelineEngine:
    """
    Five-tier Industrial Content Pipeline Executor:
    1. Research (Agent Reach)
    2. Automation (OpenCLI)
    3. Knowledge Matrix (NotebookLM)
    4. Structuring (Baoyu)
    5. Humanize (Humanizer-zh)
    """

    @staticmethod
    def humanize_text(raw_text: str) -> str:
        """
        Removes typical AI flavor, robotic connectors, and conclusion tone.
        Enforces concrete examples, spoken rhythm, and emotional nuance.
        """
        text = raw_text
        
        # 1. Elimination of banned cliché connectors and transition phrases
        banned_phrases = [
            (r"在这个快节奏的时代[，,]?", ""),
            (r"随着科技的飞速发展[，,]?", ""),
            (r"众所周知[，,]?", ""),
            (r"毋庸置疑[，,]?", ""),
            (r"总而言之[，,]?", "所以，说到底，"),
            (r"综上所述[，,]?", "一句话总结："),
            (r"不仅如此[，,]?", "更关键的是，"),
            (r"值得注意的是[，,]?", "你必须注意："),
            (r"事实上[，,]?", "但其实，"),
            (r"让我们一起来看[看]?[，,]?", ""),
            (r"根据研究表明[，,]?", "科学上早就发现，"),
            (r"极大地提升了", "直接翻倍了"),
            (r"做出了事后无比后悔的决定", "做完就恨不得抽自己耳光"),
            (r"生理故障", "恶性夺权"),
            (r"前额叶皮层供能骤降", "理智脑直接被拉闸断电")
        ]
        for pattern, replacement in banned_phrases:
            text = re.sub(pattern, replacement, text)

        # 2. Spoken breathing rhythm & break up long monotonous sentences
        text = text.replace("；", "。").replace("，也就是说，", "。说白了，")
        
        # 3. Clean duplicate punctuation and whitespace
        text = re.sub(r" +", " ", text).strip()
        return text

    @staticmethod
    def apply_baoyu_structure(theme: str, pain_points: List[str], core_mechanism: str, solution: str) -> Dict[str, Any]:
        """
        Structures a 60-second high-conversion explainer/screenplay following Baoyu's Gestalt rule:
        - Act 1: 3-Second Hook + Pain Point (0-15s)
        - Act 2: Subversion + Core Mechanism Deep-Dive (15-40s)
        - Act 3: Emotional Peak + Actionable Protocol (40-60s)
        """
        act1_narration = f"你有没有过这种经历：{pain_points[0]}？在暴怒的那几秒钟里，我们做出的决定，几乎百分之百是错的。"
        act1_narration += "很多人以为这是性格暴躁或情商低，但科学上早就证实了：这真不怪你，而是你的大脑刚刚经历了一场恶性夺权！"

        act2_narration = f"正常情况下，掌管权衡与逻辑的前额叶就像理智脑总裁。{core_mechanism}"

        act3_narration = f"但好消息是，这套暴走生理反应只能维持短短二十秒。下次火气上头，{solution}。给理智脑总裁争取二十秒撬开锁，你的理性就能重夺方向盘。"

        return {
            "theme": theme,
            "act_1": {
                "phase": "0-15s 痛点共鸣与悬念",
                "text": ContentPipelineEngine.humanize_text(act1_narration),
                "goal": "抓牢前3秒完播率，消除自责心理"
            },
            "act_2": {
                "phase": "15-40s 机制揭秘与视觉隐喻",
                "text": ContentPipelineEngine.humanize_text(act2_narration),
                "goal": "提供恍然大悟的认知增量（Aha Moment）"
            },
            "act_3": {
                "phase": "40-60s 科学破局与行动赋能",
                "text": ContentPipelineEngine.humanize_text(act3_narration),
                "goal": "给出极低门槛、人人可用的具体动作"
            }
        }
