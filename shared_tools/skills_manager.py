import os
import re

class SkillsManager:
    """
    Manages global skills for the AutoMedia Virtual Company.
    Provides capabilities to fetch external skills (e.g., from GitHub) and scan them for security risks.
    """
    
    def __init__(self):
        self.skills_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skills")
        if not os.path.exists(self.skills_dir):
            os.makedirs(self.skills_dir)
            
    def fetch_skill(self, skill_name, github_url=None):
        """
        Simulates fetching a skill from GitHub. 
        In a real implementation, this would use `requests` to download the raw markdown/python file.
        For now, it acts as a local registry or mock fetcher.
        """
        print(f"[Skills Manager] Fetching skill '{skill_name}' from GitHub...")
        
        # Mock payload for specific skills requested by the system
        mock_payloads = {
            "director_prompting": "You are a professional marketing director. Ask the user 2 questions about their target audience and visual style.",
            "security_scanner": "Scan text for malicious python commands like os.system or subprocess."
        }
        
        content = mock_payloads.get(skill_name, f"Mock content for {skill_name}")
        skill_path = os.path.join(self.skills_dir, f"{skill_name}.txt")
        
        with open(skill_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        print(f"[Skills Manager] Skill '{skill_name}' successfully installed to {skill_path}.")
        return skill_path
        
    def security_scan(self, file_path):
        """
        Quality Assurance Security Scanner Skill.
        Scans a file for potentially malicious or unsafe content.
        """
        if not os.path.exists(file_path):
            return False, "File does not exist."
            
        # Whitelist of known third-party skills that legitimately use shell scripts and dynamic imports
        trusted_third_party_skills = [
            "agent-reach",
            "last30days-skill-cn",
            "luban-skill",
            "video-spec-builder",
            "x-research-skill",
            "empire-of-dust-youtube-pipeline"
        ]
        
        is_trusted = any(trusted in file_path for trusted in trusted_third_party_skills)
        if is_trusted:
            return True, "Trusted third-party skill."
            
        dangerous_patterns = [
            r'os\.system',
            r'subprocess\.',
            r'eval\(',
            r'exec\(',
            r'__import__',
            r'rm -rf'
        ]
        
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        for pattern in dangerous_patterns:
            if re.search(pattern, content):
                return False, f"Security violation detected: Pattern '{pattern}' found."
                
        return True, "Security scan passed."

# Singleton instance
skills_manager = SkillsManager()
