import os
import re
import yaml
import subprocess

class SkillEngine:
    def __init__(self, workspace_dir=None):
        if workspace_dir is None:
            # Assumes shared_tools is inside ai-short-drama
            self.workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        else:
            self.workspace_dir = workspace_dir
            
        import glob
        self.skills_dirs = [
            os.path.join(self.workspace_dir, "skills"),
            os.path.join(os.path.dirname(self.workspace_dir), ".agents", "skills"),
            os.path.join(self.workspace_dir, ".agents", "skills")
        ]
        
        home_dir = os.path.expanduser("~")
        plugins_pattern = os.path.join(home_dir, ".gemini", "config", "plugins", "*", "skills")
        self.skills_dirs.extend(glob.glob(plugins_pattern))
        
        self.available_skills = {}
        self.active_skills_content = []
        self.discover_skills()

    def discover_skills(self):
        """Scan skills directory and parse SKILL.md files to populate available_skills"""
        for s_dir in self.skills_dirs:
            if not os.path.exists(s_dir):
                continue
                
            for item in os.listdir(s_dir):
                skill_path = os.path.join(s_dir, item)
                if os.path.isdir(skill_path):
                    # Check for SKILL.md inside the skill folder or in nested folders
                    skill_md_path = self._find_skill_md(skill_path)
                    if skill_md_path:
                        meta = self._parse_yaml_frontmatter(skill_md_path)
                        if meta and 'name' in meta:
                            # Avoid duplicates, first come first served (project > workspace > global)
                            if meta['name'] not in self.available_skills:
                                self.available_skills[meta['name']] = {
                                    "description": str(meta.get('description', 'No description')).replace('\n', ' '),
                                    "path": skill_md_path,
                                    "dir": os.path.dirname(skill_md_path)
                                }

    def _find_skill_md(self, base_dir):
        # Allow nested structure like agent_reach/skill/SKILL.md
        for root, dirs, files in os.walk(base_dir):
            if "SKILL.md" in files:
                return os.path.join(root, "SKILL.md")
        return None

    def _parse_yaml_frontmatter(self, filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
            if match:
                yaml_content = match.group(1)
                try:
                    import yaml
                    parsed = yaml.safe_load(yaml_content)
                    if isinstance(parsed, dict):
                        return parsed
                except Exception:
                    # Fallback parser
                    meta = {}
                    for line in yaml_content.split('\n'):
                        if ':' in line:
                            parts = line.split(':', 1)
                            key = parts[0].strip()
                            if key not in meta:
                                meta[key] = parts[1].strip(' \'"')
                    return meta
        except Exception as e:
            print(f"[SkillEngine] Error parsing {filepath}: {e}")
        return None

    def get_skill_catalog_prompt(self):
        prompt = "\n\n【可用核心技能库 (Available Skills)】\n"
        prompt += "如果你认为需要使用以下技能来帮助完成任务，请输出 XML 标签：<ACTIVATE_SKILL>技能名称</ACTIVATE_SKILL>。一旦输出，系统会自动将技能规则完整注入你的大脑。\n"
        for name, info in self.available_skills.items():
            prompt += f"- {name}: {info['description'][:150]}...\n"
        prompt += "\n如果你在阅读某个技能后需要执行系统命令（比如运行 Python 脚本），请输出：<RUN_COMMAND>命令</RUN_COMMAND>。系统会在后台执行并将结果返回给你。请一次只调用一个技能或命令。\n"
        return prompt

    def run_agentic_loop(self, base_system_prompt, chat_history, llm_caller):
        """
        Agentic execution loop.
        chat_history: list of dicts [{"role": "user/assistant", "content": "..."}]
        llm_caller: function(system_prompt, history_text) -> str
        """
        while True:
            # Build current system prompt dynamically
            current_system_prompt = base_system_prompt + self.get_skill_catalog_prompt()
            if self.active_skills_content:
                current_system_prompt += "\n\n【已激活的技能上下文 (Active Skills)】\n"
                for content in self.active_skills_content:
                    current_system_prompt += f"\n---\n{content}\n---\n"
            
            # Only send the last few turns to avoid context blowout, but ensure the latest internal thoughts are there
            history_text = "\n".join([f"{m['role']}: {m['content']}" for m in chat_history[-10:]])
            
            # Call LLM
            response = llm_caller(current_system_prompt, history_text)
            if not response:
                return "（LLM 接口返回空值或调用失败）"
            
            # Check for tool tags
            activate_match = re.search(r'<ACTIVATE_SKILL>(.*?)</ACTIVATE_SKILL>', response)
            cmd_match = re.search(r'<RUN_COMMAND>(.*?)</RUN_COMMAND>', response, re.DOTALL)
            
            if activate_match:
                skill_name = activate_match.group(1).strip()
                print(f" [Skill Engine] ⚡️ 动态装载技能: {skill_name} ...")
                
                chat_history.append({"role": "assistant", "content": response})
                
                if skill_name in self.available_skills:
                    skill_info = self.available_skills[skill_name]
                    try:
                        with open(skill_info['path'], 'r', encoding='utf-8') as f:
                            self.active_skills_content.append(f.read())
                        chat_history.append({"role": "user", "content": f"[System]: 技能 {skill_name} 已成功装载到你的系统上下文中，请阅读其规则并继续执行任务。你现在可以回答用户，或执行 RUN_COMMAND。"})
                    except Exception as e:
                        chat_history.append({"role": "user", "content": f"[System]: 技能装载失败: {e}"})
                else:
                    chat_history.append({"role": "user", "content": f"[System]: 技能 {skill_name} 不存在。请检查可用技能列表。"})
                
                # Continue loop to let LLM respond to the new context
                continue 
                
            elif cmd_match:
                command = cmd_match.group(1).strip()
                
                # Resolve {{SKILL_DIR}} placeholder based on actively loaded skills
                for sk_name, sk_info in self.available_skills.items():
                    command = command.replace(f"{{{{{sk_name}_DIR}}}}", sk_info['dir'])
                command = command.replace("{{SKILL_DIR}}", os.path.join(self.workspace_dir, "skills", "last30days-skill-cn")) # Default fallback

                print(f" [Skill Engine] ⚙️ 正在沙盒执行命令: {command}")
                chat_history.append({"role": "assistant", "content": response})
                
                try:
                    result = subprocess.run(
                        command, 
                        shell=True, 
                        capture_output=True, 
                        text=True,
                        cwd=self.workspace_dir,
                        timeout=60
                    )
                    stdout = result.stdout.strip()
                    stderr = result.stderr.strip()
                    out_text = f"STDOUT:\n{stdout[:2000]}" # Truncate to prevent blowouts
                    if stderr:
                        out_text += f"\nSTDERR:\n{stderr[:1000]}"
                    
                    chat_history.append({"role": "user", "content": f"<COMMAND_OUTPUT>\n{out_text}\n</COMMAND_OUTPUT>\n请根据输出向用户汇报。"})
                except Exception as e:
                    chat_history.append({"role": "user", "content": f"<COMMAND_OUTPUT>\n执行失败: {e}\n</COMMAND_OUTPUT>"})
                
                continue
            
            else:
                # No tags found, this is a final response to the user
                return response
