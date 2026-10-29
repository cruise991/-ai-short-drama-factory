import re
import logging
from typing import List, Tuple, Dict, Any, Set, Optional

logger = logging.getLogger("ComplianceEngine")

# 默认内置敏感词与广告法禁用词库
DEFAULT_PROHIBITED_WORDS = [
    # 广告法极限词 (Advertising Law Absolute Words)
    "第一", "国家级", "世界级", "顶级", "最高级", "最佳", "最大", "最新技术", "最先进",
    "独家首创", "全网首发", "绝无仅有", "史无前例", "永久免费", "包治百病", "药到病除",
    "100%有效", "绝不反弹", "买到就是赚到", "暴富",
    # 涉欺诈与违规 (Fraud & Inappropriate)
    "刷单", "假货", "洗钱", "赌博", "诈骗", "透视外挂", "代开发票"
]

class DFASensitiveFilter:
    """
    基于确定有穷自动机 (DFA) 的高性能敏感词前缀树过滤算法。
    支持在毫秒级时间内对长文本完成高并发多模式匹配。
    """
    def __init__(self, words: Optional[List[str]] = None):
        self.root: Dict[str, Any] = {}
        self.end_mark = "\x00"
        self.load_words(words or DEFAULT_PROHIBITED_WORDS)

    def load_words(self, words: List[str]):
        for word in words:
            word = word.strip()
            if not word:
                continue
            current = self.root
            for char in word:
                if char not in current:
                    current[char] = {}
                current = current[char]
            current[self.end_mark] = True

    def find_all(self, text: str) -> List[Tuple[str, int]]:
        """查找文本中所有出现的敏感词及其位置"""
        hits = []
        n = len(text)
        i = 0
        while i < n:
            current = self.root
            j = i
            matched_word = ""
            last_hit = None

            while j < n and text[j] in current:
                char = text[j]
                matched_word += char
                current = current[char]
                if self.end_mark in current:
                    last_hit = (matched_word, i)
                j += 1

            if last_hit:
                hits.append(last_hit)
                i += len(last_hit[0]) # 跳过已匹配词
            else:
                i += 1
        return hits

    def mask(self, text: str, mask_char: str = "*") -> str:
        """将敏感词替换为指定掩码字符"""
        hits = self.find_all(text)
        if not hits:
            return text
        chars = list(text)
        for word, start in hits:
            for idx in range(start, start + len(word)):
                chars[idx] = mask_char
        return "".join(chars)

    def is_clean(self, text: str) -> Tuple[bool, List[str]]:
        """检查文本是否合规，若不合规返回命中的违禁词列表"""
        hits = self.find_all(text)
        violations = list(set([h[0] for h in hits]))
        return (len(violations) == 0, violations)

# 全局单例
sensitive_filter = DFASensitiveFilter()

def audit_text_compliance(text: str) -> Dict[str, Any]:
    """
    通用文本合规审计入口。
    可用于弹幕过滤、主播回复审查、话术脚本入库前置校验。
    """
    is_clean, violations = sensitive_filter.is_clean(text)
    masked = sensitive_filter.mask(text) if not is_clean else text
    return {
        "is_compliant": is_clean,
        "violations": violations,
        "masked_text": masked,
        "original_text": text
    }
