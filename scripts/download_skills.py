import os
import urllib.request
import ssl

def download_skill(name, url):
    # Determine absolute path to workspace root based on this script's location
    base_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_root = os.path.dirname(base_dir) # Should point to /Users/workspace/ai_short_company
    
    skill_dir = os.path.join(workspace_root, ".agents", "skills", name)
    os.makedirs(skill_dir, exist_ok=True)
    
    skill_file_path = os.path.join(skill_dir, "SKILL.md")
    
    print(f"Downloading {name} from {url}...")
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ctx) as response:
            content = response.read().decode('utf-8')
            with open(skill_file_path, "w", encoding="utf-8") as f:
                f.write(content)
        print(f"✅ Successfully downloaded {name} to {skill_file_path}")
    except Exception as e:
        print(f"❌ Failed to download {name}: {e}")

if __name__ == "__main__":
    print("--- 启动技能全自动下载同步程序 ---")
    
    # 1. 真实下载: qu-ai-wei 去AI味洗稿技能
    download_skill(
        "qu_ai_wei", 
        "https://raw.githubusercontent.com/LifelongLazyLearner/qu-ai-wei/main/SKILL.md"
    )
    
    # 2. 真实下载: nuwa-skill 女娲人格蒸馏技能
    download_skill(
        "nuwa_skill", 
        "https://raw.githubusercontent.com/alchaincyf/nuwa-skill/main/SKILL.md"
    )
    
    print("--- 同步完成！ ---")
