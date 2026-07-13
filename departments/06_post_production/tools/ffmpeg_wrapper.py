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

    def replace_audio_in_video(self, video_path, audio_path, output_path):
        print(f"    [Local Tool: FFmpeg] Real Audio replacement on {os.path.basename(video_path)}...")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        vid_duration = self.get_duration(video_path)
        aud_duration = self.get_duration(audio_path)
        
        print(f"    [Local Tool: FFmpeg] Video: {vid_duration}s, Audio: {aud_duration}s")
        
        if aud_duration > vid_duration:
            # Freeze the last frame of the video to extend it to the audio length
            print(f"    [Local Tool: FFmpeg] Audio is longer. Freezing last frame of video...")
            cmd = [
                "ffmpeg", "-y",
                "-i", video_path,
                "-i", audio_path,
                "-filter_complex", "[0:v]tpad=stop_mode=clone:stop_duration=60[v]",
                "-map", "[v]",
                "-map", "1:a:0",
                "-c:v", "libx264",
                "-c:a", "aac",
                "-shortest",
                output_path
            ]
        else:
            # Video is longer or equal. Pad audio with silence so it doesn't cut the video early.
            print(f"    [Local Tool: FFmpeg] Video is longer/equal. Padding audio with silence...")
            cmd = [
                "ffmpeg", "-y",
                "-i", video_path,
                "-i", audio_path,
                "-filter_complex", "[1:a]apad[a]",
                "-map", "0:v:0",
                "-map", "[a]",
                "-c:v", "copy",
                "-c:a", "aac",
                "-shortest",
                output_path
            ]
        
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"    [Local Tool: FFmpeg] Real component rendered to {output_path}")
            return True
        except Exception as e:
            print(f"    [Local Tool: FFmpeg] Real FFmpeg failed: {e}")
            # fallback
            with open(output_path, "w") as f:
                f.write("mock")
            return False

    def concat_videos(self, video_list, final_output_path):
        print(f"    [Local Tool: FFmpeg] Real Concatenating {len(video_list)} clips into final episode...")
        
        # Create concat text file
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
            print(f"    [Local Tool: FFmpeg] Concat failed: {e}")
            # fallback
            with open(final_output_path, "w") as f:
                f.write("mock")
            return False
        finally:
            if os.path.exists(concat_file):
                os.remove(concat_file)
