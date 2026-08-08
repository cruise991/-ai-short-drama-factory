import os
import subprocess

def robust_video_concat(video_files, bgm_path, output_mp4):
    list_txt = output_mp4 + ".list.txt"
    temp_video = output_mp4 + ".temp_v.mp4"
    
    with open(list_txt, "w") as f:
        for v in video_files:
            f.write(f"file '{os.path.abspath(v)}'\n")

    # Step 1: Pure video re-encode (H.264 yuv420p 24fps)
    cmd1 = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", list_txt,
        "-an",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "24",
        temp_video
    ]
    subprocess.run(cmd1, check=True)

    # Step 2: Mux single continuous audio stream (AAC stereo 192k)
    cmd2 = [
        "ffmpeg", "-y",
        "-i", temp_video,
        "-i", bgm_path,
        "-c:v", "copy",
        "-c:a", "aac", "-ac", "2", "-b:a", "192k",
        "-shortest",
        output_mp4
    ]
    subprocess.run(cmd2, check=True)

    if os.path.exists(temp_video): os.remove(temp_video)
    if os.path.exists(list_txt): os.remove(list_txt)
    return output_mp4
