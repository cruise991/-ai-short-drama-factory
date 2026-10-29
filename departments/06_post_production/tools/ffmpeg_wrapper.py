import os
import subprocess

class FFmpegWrapper:
    """
    Department-level FFmpeg Wrapper running REAL local ffmpeg commands.
    """
    
    def __init__(self):
        pass

    def get_duration(self, filepath):
        cmd = [
            "ffprobe", "-v", "error", "-show_entries",
            "format=duration", "-of",
            "default=noprint_wrappers=1:nokey=1", filepath
        ]
        try:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            return float(result.stdout.strip())
        except Exception as e:
            print(f"    [Local Tool: FFmpeg] Failed to get duration for {filepath}: {e}")
            return 5.0 # default fallback

    def trim_video(self, video_path, duration, output_path):
        print(f"    [Local Tool: FFmpeg] Trimming {video_path} to {duration}s...")
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-t", str(duration),
            "-c:v", "libx264", # re-encode to ensure keyframes are handled
            output_path
        ]
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception as e:
            print(f"    [Local Tool: FFmpeg] Trim failed: {e}")
            import shutil
            shutil.copy2(video_path, output_path)
            return False

    def trim_video_start(self, video_path, start_time, output_path):
        print(f"    [Local Tool: FFmpeg] Trimming {video_path} starting from {start_time}s...")
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(start_time),
            "-i", video_path,
            "-c:v", "libx264",
            output_path
        ]
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception as e:
            print(f"    [Local Tool: FFmpeg] Trim start failed: {e}")
            import shutil
            shutil.copy2(video_path, output_path)
            return False

    def _format_subtitle_text(self, text: str, max_chars: int = 14) -> str:
        """
        智能短剧字幕折行与排版：
        短视频单行字幕保持在 12-16 汉字最佳阅读区间。
        若超过 max_chars，优先在标点处断句换行，保证移动端居中对称美观。
        """
        clean = text.strip()
        if len(clean) <= max_chars:
            return clean
        puncts = ['？', '！', '，', '。', '…', '?', '!', ',']
        for p in puncts:
            idx = clean.find(p)
            if 4 <= idx <= max_chars + 2:
                return clean[:idx+1] + "\n" + clean[idx+1:].strip()
        mid = len(clean) // 2
        return clean[:mid] + "\n" + clean[mid:].strip()

    def replace_audio_in_video(self, video_path, audio_path, output_path, subtitle_text=None):
        print(f"    [Local Tool: FFmpeg] Real Audio replacement on {os.path.basename(video_path)}...")
    def get_video_dimensions(self, filepath):
        cmd = [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=width,height", "-of", "csv=s=x:p=0",
            filepath
        ]
        try:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            parts = result.stdout.strip().split("x")
            return int(parts[0]), int(parts[1])
        except Exception:
            return 1080, 1920

    def replace_audio_in_video(self, video_path, audio_path, output_path, subtitle_text=None):
        print(f"    [Local Tool: FFmpeg] Real Audio replacement on {os.path.basename(video_path)}...")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        vid_duration = self.get_duration(video_path)
        aud_duration = self.get_duration(audio_path)
        w, h = self.get_video_dimensions(video_path)
        is_landscape = (w / h) > 0.65  # 16:9 / 4:3 / 1:1 等横版比例，触发动态高斯弥散毛玻璃背景
        
        print(f"    [Local Tool: FFmpeg] Video: {vid_duration}s ({w}x{h}, landscape={is_landscape}), Audio: {aud_duration}s")
        
        # 基础视频画幅处理：如果是横屏素材，使用高端动态毛玻璃/高斯弥散背景填充，彻底消除上下压抑死黑边；如果是原生9:16则保持无缝铺满
        if is_landscape:
            base_v_filter = (
                "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=25:5,eq=brightness=-0.12[bg];"
                "[0:v]scale=1080:1920:force_original_aspect_ratio=decrease[fg];"
                "[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1,fps=25"
            )
        else:
            base_v_filter = "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=25"
        
        # 查找商用高清中文字体
        text_file = None
        font_path = "/workspace/assets/fonts/STHeitiMedium.ttc"
        if not os.path.exists(font_path):
            alt_font = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "assets", "fonts", "STHeitiMedium.ttc")
            if os.path.exists(alt_font):
                font_path = alt_font

        if subtitle_text and os.path.exists(font_path):
            formatted_text = self._format_subtitle_text(subtitle_text)
            text_file = output_path + ".sub.txt"
            with open(text_file, "w", encoding="utf-8") as tf:
                tf.write(formatted_text)
            safe_tf = text_file.replace(":", "\\:").replace("'", "\\'")
            safe_font = font_path.replace(":", "\\:").replace("'", "\\'")
            sub_end = max(vid_duration, aud_duration)
            drawtext_str = (
                f",drawtext=fontfile='{safe_font}':textfile='{safe_tf}':"
                f"fontsize=54:fontcolor=white:borderw=4:bordercolor=black:"
                f"line_spacing=12:x=(w-text_w)/2:y=h-text_h-460:"
                f"enable='between(t,0,{sub_end:.2f})'"
            )
            base_v_filter += drawtext_str
            print(f"    [Local Tool: FFmpeg] ✨ Burned-in subtitle: '{subtitle_text}'")

        try:
            if aud_duration > vid_duration:
                # 冻结最后一帧补齐视频时长
                print(f"    [Local Tool: FFmpeg] Audio is longer. Freezing last frame of video...")
                cmd = [
                    "ffmpeg", "-y",
                    "-i", video_path,
                    "-i", audio_path,
                    "-filter_complex", f"{base_v_filter},tpad=stop_mode=clone:stop_duration=60[v]",
                    "-map", "[v]",
                    "-map", "1:a:0",
                    "-c:v", "libx264",
                    "-preset", "fast",
                    "-crf", "20",
                    "-pix_fmt", "yuv420p",
                    "-c:a", "aac",
                    "-ar", "44100",
                    "-ac", "2",
                    "-shortest",
                    output_path
                ]
            else:
                # 视频较长或等长，音频补齐静音
                print(f"    [Local Tool: FFmpeg] Video is longer/equal. Padding audio with silence...")
                cmd = [
                    "ffmpeg", "-y",
                    "-i", video_path,
                    "-i", audio_path,
                    "-filter_complex", f"{base_v_filter}[v];[1:a]apad[a]",
                    "-map", "[v]",
                    "-map", "[a]",
                    "-c:v", "libx264",
                    "-preset", "fast",
                    "-crf", "20",
                    "-pix_fmt", "yuv420p",
                    "-c:a", "aac",
                    "-ar", "44100",
                    "-ac", "2",
                    "-shortest",
                    output_path
                ]
            
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"    [Local Tool: FFmpeg] Real component rendered to {output_path}")
            return True
        except Exception as e:
            print(f"    [Local Tool: FFmpeg] Real FFmpeg failed: {e}")
            return False
        finally:
            if text_file and os.path.exists(text_file):
                try:
                    os.remove(text_file)
                except:
                    pass

    def normalize_silent_video(self, video_path, output_path, subtitle_text=None):
        """为无旁白视频生成标准化 1080x1920 25fps 并添加对齐的静音音频轨（支持高斯弥散背景与字幕烧录）"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        dur = self.get_duration(video_path)
        w, h = self.get_video_dimensions(video_path)
        is_landscape = (w / h) > 0.65
        
        if is_landscape:
            base_v_filter = (
                "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=25:5,eq=brightness=-0.12[bg];"
                "[0:v]scale=1080:1920:force_original_aspect_ratio=decrease[fg];"
                "[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1,fps=25"
            )
        else:
            base_v_filter = "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=25"
        
        text_file = None
        font_path = "/workspace/assets/fonts/STHeitiMedium.ttc"
        if not os.path.exists(font_path):
            alt_font = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "assets", "fonts", "STHeitiMedium.ttc")
            if os.path.exists(alt_font):
                font_path = alt_font

        if subtitle_text and os.path.exists(font_path):
            formatted_text = self._format_subtitle_text(subtitle_text)
            text_file = output_path + ".sub.txt"
            with open(text_file, "w", encoding="utf-8") as tf:
                tf.write(formatted_text)
            safe_tf = text_file.replace(":", "\\:").replace("'", "\\'")
            safe_font = font_path.replace(":", "\\:").replace("'", "\\'")
            drawtext_str = (
                f",drawtext=fontfile='{safe_font}':textfile='{safe_tf}':"
                f"fontsize=54:fontcolor=white:borderw=4:bordercolor=black:"
                f"line_spacing=12:x=(w-text_w)/2:y=h-text_h-460:"
                f"enable='between(t,0,{dur:.2f})'"
            )
            base_v_filter += drawtext_str

        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=stereo",
            "-filter_complex", f"{base_v_filter}[v]",
            "-map", "[v]",
            "-map", "1:a",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "20",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-ar", "44100",
            "-ac", "2",
            "-shortest",
            output_path
        ]
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"    [Local Tool: FFmpeg] Normalized silent video to {output_path}")
            return True
        except Exception as e:
            print(f"    [Local Tool: FFmpeg] Silent normalization failed: {e}")
            import shutil
            shutil.copy2(video_path, output_path)
            return False
        finally:
            if text_file and os.path.exists(text_file):
                try:
                    os.remove(text_file)
                except:
                    pass

    def concat_videos(self, video_list, final_output_path):
        print(f"    [Local Tool: FFmpeg] Real Concatenating {len(video_list)} clips into final episode...")
        os.makedirs(os.path.dirname(final_output_path), exist_ok=True)
        
        # 方式 1: concat demuxer
        concat_file = final_output_path + ".txt"
        with open(concat_file, "w") as f:
            for vid in video_list:
                f.write(f"file '{os.path.abspath(vid)}'\n")
                
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_file,
            "-c", "copy",
            final_output_path
        ]
        
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"    [Local Tool: FFmpeg] Real final video exported successfully to {final_output_path}!")
            return True
        except Exception as e:
            print(f"    [Local Tool: FFmpeg] Concat copy failed ({e}), switching to filter_complex concat re-encoding...")
            # 方式 2: filter_complex 终极重编码自愈兜底
            try:
                inputs = []
                filter_parts = []
                for i, vid in enumerate(video_list):
                    inputs.extend(["-i", vid])
                    filter_parts.append(f"[{i}:v:0][{i}:a:0]")
                filter_complex = "".join(filter_parts) + f"concat=n={len(video_list)}:v=1:a=1[outv][outa]"
                reencode_cmd = [
                    "ffmpeg", "-y", *inputs,
                    "-filter_complex", filter_complex,
                    "-map", "[outv]", "-map", "[outa]",
                    "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-ar", "44100", "-ac", "2",
                    final_output_path
                ]
                subprocess.run(reencode_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print(f"    [Local Tool: FFmpeg] Re-encoded concat succeeded: {final_output_path}")
                return True
            except Exception as e2:
                print(f"    [Local Tool: FFmpeg] Filter concat failed: {e2}")
                return False
        finally:
            if os.path.exists(concat_file):
                os.remove(concat_file)
