import os
import sys
import json
import time
import random
import sys

def get_config(key, default=""):
    import dotenv
    dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env")
    dotenv.load_dotenv(dotenv_path)
    return os.getenv(key, default)

workspace_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if workspace_dir not in sys.path:
    sys.path.insert(0, workspace_dir)

from shared_tools.api_pool import call_llm

def simulate_market_data():
    """Simulate pulling data from a social media platform API (TikTok/Xiaohongshu)"""
    views = random.randint(500, 5000000)
    completion_rate = round(random.uniform(5.0, 60.0), 2) # 5% to 60%
    conversion_rate = round(random.uniform(0.1, 5.0), 2)  # 0.1% to 5%
    
    # Define thresholds
    is_hit = completion_rate > 30.0 and conversion_rate > 2.0 and views > 100000
    is_flop = completion_rate < 10.0 or conversion_rate < 0.5
    
    return {
        "views": views,
        "completion_rate": completion_rate,
        "conversion_rate": conversion_rate,
        "is_hit": is_hit,
        "is_flop": is_flop
    }

def update_memory(new_rule, is_positive):
    memory_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "company_memory.json")
    try:
        with open(memory_path, "r", encoding="utf-8") as f:
            memory = json.load(f)
    except:
        memory = {"positive_patterns": [], "negative_patterns": []}
        
    key = "positive_patterns" if is_positive else "negative_patterns"
    if new_rule and new_rule not in memory[key]:
        memory[key].append(new_rule)
        
        # Simple compression protection (assuming compress_memory is handled by QA during run, or we do a simple slice here, but protect CEO)
        ceo_rules = [r for r in memory[key] if "[CEO]" in r]
        auto_rules = [r for r in memory[key] if "[CEO]" not in r]
        memory[key] = ceo_rules + auto_rules[-5:]
        
        with open(memory_path, "w", encoding="utf-8") as f:
            json.dump(memory, f, ensure_ascii=False, indent=2)
        print(f"  [Market Feedback Dept] Saved new {'POSITIVE' if is_positive else 'NEGATIVE'} memory: {new_rule}")

def process_ticket(episode_dir):
    ticket_path = os.path.join(episode_dir, "00_task_ticket.json")
    if not os.path.exists(ticket_path):
        return False
        
    with open(ticket_path, "r", encoding="utf-8") as f:
        ticket = json.load(f)
        
    if ticket.get("status") != "Market_Testing":
        return False
        
    print(f"\n[Market Feedback Dept] Fetching market data for: {ticket.get('goal')} ...")
    time.sleep(2) # Simulate API delay
    
    data = simulate_market_data()
    print(f"  📊 播放量: {data['views']}")
    print(f"  📈 完播率: {data['completion_rate']}%")
    print(f"  💰 转化率: {data['conversion_rate']}%")
    
    format_type = ticket.get("format_type", "旁白演绎")
    is_dance_format = "舞蹈" in format_type or "钩子" in format_type

    if data["is_hit"] or data["is_flop"]:
        script_path = os.path.join(episode_dir, "01_storyboards_scripts", "01_storyboard.md")
        script_content = ""
        if os.path.exists(script_path):
            with open(script_path, "r", encoding="utf-8") as f:
                script_content = f.read()
                
        if is_dance_format:
            # --- Dance Factory Growth Loop ---
            print("  🌀 识别到【Dance Factory】分支，启动 Combo Pair 自动进化...")
            combo_memory_path = os.path.join(workspace_dir, "departments", "00_global_data", "combo_memory.json")
            try:
                with open(combo_memory_path, "r", encoding="utf-8") as f:
                    combo_mem = json.load(f)
            except:
                combo_mem = {"combos": {}}
                
            try:
                prompt = f"这个短视频剧本属于舞蹈分支。请提取出其中用到的核心组合特征，返回一个纯JSON对象。必须包含以下字段（如果没有则留空）：character, setup_outfit, hook_outfit, routine, scene, bgm_id。不要输出其他废话，直接输出JSON。\n\n剧本内容：\n{script_content}"
                combo_str = call_llm("你是一个提取器。", prompt)
                
                import re
                json_match = re.search(r'\{.*\}', combo_str, re.DOTALL)
                if json_match:
                    combo_data = json.loads(json_match.group(0))
                    
                    # Hash the combo
                    import hashlib
                    combo_str_for_hash = f"{combo_data.get('character')}_{combo_data.get('setup_outfit')}_{combo_data.get('hook_outfit')}_{combo_data.get('routine')}_{combo_data.get('bgm_id')}"
                    combo_id = hashlib.md5(combo_str_for_hash.encode()).hexdigest()[:8]
                    
                    if combo_id not in combo_mem["combos"]:
                        combo_mem["combos"][combo_id] = {
                            "features": combo_data,
                            "weight": 1.0,
                            "history": []
                        }
                    
                    old_weight = combo_mem["combos"][combo_id]["weight"]
                    if data["is_hit"]:
                        new_weight = min(10.0, old_weight + 1.0)
                        print(f"    📈 爆款奖赏: Combo {combo_id} 权重提升 {old_weight} -> {new_weight}")
                    else:
                        new_weight = max(0.1, old_weight - 1.0)
                        print(f"    📉 劣质惩罚: Combo {combo_id} 权重下降 {old_weight} -> {new_weight}")
                        
                    combo_mem["combos"][combo_id]["weight"] = new_weight
                    combo_mem["combos"][combo_id]["history"].append({
                        "views": data["views"], 
                        "completion_rate": data["completion_rate"],
                        "is_hit": data["is_hit"],
                        "is_flop": data["is_flop"]
                    })
                    
                    with open(combo_memory_path, "w", encoding="utf-8") as f:
                        json.dump(combo_mem, f, ensure_ascii=False, indent=2)
                    print("  ✅ 组合记忆库 (combo_memory.json) 更新完毕！")
            except Exception as e:
                print(f"  ❌ Combo 更新失败: {e}")
                
        else:
            # --- Standard Script Growth Loop ---
            if data["is_hit"]:
                print("  🎉 判定为【爆款】！正在剖析成功基因...")
                prompt = f"这个短视频剧本在市场投放中大获成功（完播率和转化率极高）。请深度剖析其结构，提炼出【1条】不超过30字的【正向营销法则】（例如某种特定的钩子、视觉反差或台词节奏）。直接输出法则本身。\n\n剧本内容：\n{script_content}"
                rule = call_llm("你是一个顶级的爆款内容拆解专家。", prompt)
                if rule:
                    update_memory(rule.strip(), is_positive=True)
                    
            elif data["is_flop"]:
                print("  📉 判定为【劣质内容】！正在反思避坑教训...")
                prompt = f"这个短视频剧本在市场投放中数据极差（完播率或转化率垫底）。请深度剖析其结构，提炼出【1条】不超过30字的【负向避坑法则】（例如前3秒拖沓、产品展示生硬等）。直接输出法则本身。\n\n剧本内容：\n{script_content}"
                rule = call_llm("你是一个严厉的营销复盘专家。", prompt)
                if rule:
                    update_memory(rule.strip(), is_positive=False)
    else:
        print("  ⚖️ 数据平庸，无明显可提炼的极端特征。跳过演进记忆提取。")

    # Update state to completed
    ticket["status"] = "Completed"
    ticket["last_updated_by"] = "Market_Feedback_Agent"
    ticket["last_updated_time"] = time.time()
    
    with open(ticket_path, "w", encoding="utf-8") as f:
        json.dump(ticket, f, ensure_ascii=False, indent=2)
        
    print("[Market Feedback Dept] Market testing complete. Status advanced to Completed.")
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_dir = sys.argv[1]
    else:
        workspace_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        run_dir = os.path.join(workspace_dir, "projects", "paperai-series", "episode-01")
    process_ticket(run_dir)
