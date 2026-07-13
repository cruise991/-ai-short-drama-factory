import re
import os

with open("/Users/workspace/ai_short_company /ai-short-drama/departments/03_production/production_agent.py", "r") as f:
    content = f.read()

process_ticket_end = """
        has_error = False
        error_msg = ""
        
        if is_dance:
            print(f"\\n[Production Dept] Dispatching {len(shots)} shots SEQUENTIALLY (Dance Keyframe Chaining)...")
            anchor_img_url = None
            last_video_path = None
            
            for shot in shots:
                success, msg, img_url = process_single_shot(shot, anchor_img_url, last_video_path)
                if not success:
                    has_error = True
                    error_msg += msg + "\\n"
                    break
                
                anchor_img_url = img_url
                last_video_path = os.path.join(assets_dir, f"{shot['id']}.mp4")
                time.sleep(2) # Pacemaker
        else:
            print(f"\\n[Production Dept] Dispatching {len(shots)} shots concurrently...")
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                future_to_shot = {executor.submit(process_single_shot, shot): shot for shot in shots}
                for future in concurrent.futures.as_completed(future_to_shot):
                    shot = future_to_shot[future]
                    try:
                        success, msg, _ = future.result()
                        if not success:
                            has_error = True
                            error_msg += msg + "\\n"
                    except Exception as exc:
                        print(f"[Production Dept] Shot {shot['id']} generated an exception: {exc}")
                        has_error = True
                        error_msg += f"Exception processing {shot['id']}: {exc}\\n"
                        
        if has_error:
            ticket["status"] = "Paused_By_Error"
            ticket["error_message"] = error_msg.strip()
            with open(ticket_path, "w", encoding="utf-8") as f:
                json.dump(ticket, f, ensure_ascii=False, indent=2)
            return False
            
    except Exception as e:
        print(f"[Production Dept] Exception occurred: {str(e)}")
        ticket["status"] = "Paused_By_Error"
        ticket["error_message"] = f"Production Error: {str(e)}"
        with open(ticket_path, "w", encoding="utf-8") as f:
            json.dump(ticket, f, indent=4, ensure_ascii=False)
        return False
        
    # 3. Update Ticket Status to QA_Pending_Production
    ticket["status"] = "QA_Pending_Production"
    ticket["last_updated_by"] = "Production_Agent_AgnesAI"
    ticket["last_updated_time"] = time.time()
    
    with open(ticket_path, "w", encoding="utf-8") as f:
        json.dump(ticket, f, ensure_ascii=False, indent=2)
        
    print("\\n[Production Dept] Real Generation Complete. Status updated to QA_Pending_Production.")
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_dir = sys.argv[1]
    else:
        workspace_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        run_dir = os.path.join(workspace_dir, "projects", "paperai-series", "episode-01")
    process_ticket(run_dir)
"""

match_idx = content.find("        return True, \"\", img_url")
if match_idx != -1:
    new_content = content[:match_idx + len("        return True, \"\", img_url")] + "\n" + process_ticket_end
    with open("/Users/workspace/ai_short_company /ai-short-drama/departments/03_production/production_agent.py", "w") as f:
        f.write(new_content)
    print("Fixed!")
else:
    print("Could not find anchor")
