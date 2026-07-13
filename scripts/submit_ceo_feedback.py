import sys
import json
import os
import requests

def get_config(key, default=""):
    import dotenv
    dotenv.load_dotenv()
    return os.getenv(key, default)

from shared_tools.llm_pool import call_llm

def update_memory(feedback):
    memory_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "departments", "company_memory.json")
    try:
        with open(memory_path, "r", encoding="utf-8") as f:
            memory = json.load(f)
    except:
        memory = {"positive_patterns": [], "negative_patterns": []}
        
    prompt = f"""你是一个公司的战略级记忆提炼模块。
CEO 给出了对最近输出的评价。你的任务是分析这段评价，并提取成高度浓缩的规则（少于30字），分类为正向记忆（Positive Pattern: 必须坚持的做法）或负向记忆（Negative Pattern: 必须避免的做法）。
如果评价只有正面，就只返回正向规则；如果只有负面，就只返回负面规则。

CEO 评价："{feedback}"

请严格以 JSON 格式输出，不要包含 Markdown 代码块（如 ```json），直接返回可解析的字符串：
{{
  "positive": ["规则1"],
  "negative": ["规则2"]
}}
"""
    result = call_llm("你是一个专门压缩并提取系统教训的 AI，确保记忆消耗极低的Token。", prompt)
    if not result:
        print("提炼失败。")
        return
        
    try:
        # 清理可能包含的 Markdown 标记
        if result.startswith("```json"):
            result = result[7:]
        if result.startswith("```"):
            result = result[3:]
        if result.endswith("```"):
            result = result[:-3]
            
        parsed = json.loads(result.strip())
        
        pos = parsed.get("positive", [])
        neg = parsed.get("negative", [])
        
        # Tag CEO rules
        pos = [f"[CEO] {p}" if not p.startswith("[CEO]") else p for p in pos]
        neg = [f"[CEO] {n}" if not n.startswith("[CEO]") else n for n in neg]
        
        if pos:
            memory["positive_patterns"].extend(pos)
            memory["positive_patterns"] = memory["positive_patterns"][-10:]
            print(f"✅ 提取正向记忆: {pos}")
        if neg:
            memory["negative_patterns"].extend(neg)
            memory["negative_patterns"] = memory["negative_patterns"][-10:]
            print(f"❌ 提取负向记忆: {neg}")
            
        with open(memory_path, "w", encoding="utf-8") as f:
            json.dump(memory, f, ensure_ascii=False, indent=2)
            
        print("系统记忆已全量更新。下一次执行 Orchestrator 将自动生效。")
        
    except Exception as e:
        print(f"解析大模型返回结果时出错: {e}\n原始返回:\n{result}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用方法: python3 submit_ceo_feedback.py \"你的主观评价或意见\"")
        sys.exit(1)
    update_memory(sys.argv[1])
