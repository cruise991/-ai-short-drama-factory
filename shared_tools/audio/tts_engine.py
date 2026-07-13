import os
import subprocess
import shutil
import sys

class TTSEngine:
    """
    Global Text-to-Speech Engine using high-quality Neural TTS (edge-tts)
    with a seamless fallback to macOS native 'say' command (Ting-Ting).
    """
    
    def __init__(self, api_key=None):
        self.api_key = api_key
        try:
            import edge_tts
            self.has_edge_tts = True
        except ImportError:
            self.has_edge_tts = False

    def generate_audio(self, text, output_filepath, voice_id="zh-CN-XiaoxiaoNeural"):
        os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
        
        if self.has_edge_tts:
            print(f"    [Global Tool: TTS] Real synthesis using Edge-TTS ({voice_id}): '{text[:30]}...'")
            try:
                # edge-tts supports direct output to mp3 or wav
                subprocess.run([sys.executable, "-m", "edge_tts", "--voice", voice_id, "--text", text, "--write-media", output_filepath], check=True)
                print(f"    [Global Tool: TTS] Successfully saved neural audio to {output_filepath}")
                return True
            except Exception as e:
                print(f"    [Global Tool: TTS] Failed Edge-TTS, falling back to macOS 'say': {e}")
                # Fallthrough to macOS say
                
        # macOS Fallback
        mac_voice = "Ting-Ting" # High quality Chinese voice built into macOS
        if "Yunxi" in voice_id or "Male" in voice_id:
            mac_voice = "Yunjian" # macOS Chinese male voice
            
        print(f"    [Global Tool: TTS] Real synthesis using macOS 'say' ({mac_voice}): '{text[:30]}...'")
        
        # say outputs aiff by default, we'll output raw aiff but name it .aiff
        actual_output = output_filepath.replace(".wav", ".aiff")
        actual_output = actual_output.replace(".mp3", ".aiff")
        
        try:
            # macOS native TTS command
            subprocess.run(["say", "-v", mac_voice, "-o", actual_output, text], check=True)
            # rename for standard processing
            if os.path.exists(actual_output):
                os.rename(actual_output, output_filepath)
            print(f"    [Global Tool: TTS] Successfully saved real audio to {output_filepath}")
            return True
        except Exception as e:
            print(f"    [Global Tool: TTS] Failed real TTS: {e}")
            # Mock fallback if it fails
            with open(output_filepath, "w") as f:
                f.write("mock")
            return False
