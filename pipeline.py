import urllib.request
import json
import os
import subprocess
import time
import ssl
import cv2
import numpy as np
import os
import subprocess
import time
import ssl

ctx = ssl.create_default_context()
if os.environ.get("SKIP_TLS_VERIFY"):
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

API_KEY = os.environ.get("AGNES_API_KEY")
if not API_KEY:
    print("Warning: AGNES_API_KEY not found in environment")
ASSETS_DIR = "projects/paperai-series/episode-01/02_raw_assets"
FINAL_DIR = "projects/paperai-series/episode-01/04_final_output"
OUT_DIR = "../out"

os.makedirs(ASSETS_DIR, exist_ok=True)
os.makedirs(FINAL_DIR, exist_ok=True)
os.makedirs(OUT_DIR, exist_ok=True)

def fetch_json(url, data=None):
    req = urllib.request.Request(url)
    req.add_header('Authorization', f'Bearer {API_KEY}')
    req.add_header('Content-Type', 'application/json')
    if data:
        data = json.dumps(data).encode('utf-8')
    with urllib.request.urlopen(req, data=data, context=ctx) as res:
        return json.loads(res.read().decode('utf-8'))

def download(url, filename):
    print(f"Downloading {url} to {filename}")
    with urllib.request.urlopen(url, context=ctx) as response, open(filename, 'wb') as out_file:
        out_file.write(response.read())

def check_face_morphing(video_path):
    print(f"  [QA] Checking face morphing and SSIM for {video_path}")
    cap = cv2.VideoCapture(video_path)
    frames = []
    while True:
        ret, frame = cap.read()
        if not ret: break
        frames.append(frame)
    cap.release()
    
    if len(frames) < 2: return True
    
    first_frame = frames[0]
    last_frame = frames[-1]
    
    try:
        from skimage.metrics import structural_similarity as ssim
        gray_first = cv2.cvtColor(first_frame, cv2.COLOR_BGR2GRAY)
        gray_last = cv2.cvtColor(last_frame, cv2.COLOR_BGR2GRAY)
        global_score, _ = ssim(gray_first, gray_last, full=True)
    except:
        mse = np.mean((first_frame.astype("float") - last_frame.astype("float")) ** 2)
        global_score = 1.0 - (mse / 255.0**2)
        
    print(f"  [QA] Global similarity score: {global_score:.3f}")
    
    try:
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        gray_first = cv2.cvtColor(first_frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray_first, 1.1, 4)
        
        if len(faces) > 0:
            x, y, w, h = faces[0]
            face_first = gray_first[y:y+h, x:x+w]
            face_last = cv2.cvtColor(last_frame, cv2.COLOR_BGR2GRAY)[y:y+h, x:x+w]
            try:
                face_score, _ = ssim(face_first, face_last, full=True)
            except:
                mse = np.mean((face_first.astype("float") - face_last.astype("float")) ** 2)
                face_score = 1.0 - (mse / 255.0**2)
            print(f"  [QA] Facial similarity score: {face_score:.3f}")
            
            if face_score < 0.95:
                print("  [QA] 🚨 面部变异(Face Morphing)检测失败！需要重试。")
                return False
    except Exception as e:
        print(f"  [QA] Face detection failed: {e}")
            
    if global_score < 0.85:
        print("  [QA] 🚨 全局一致性检测失败！需要重试。")
        return False
        
    return True

def poll_video(task_id, filename):
    while True:
        res = fetch_json(f"https://apihub.agnes-ai.com/agnesapi?video_id={task_id}")
        status = res.get('status')
        print(f"Task {task_id} status: {status}")
        if status == 'completed':
            download(res.get('remixed_from_video_id'), filename)
            
            if "shot_01" in filename or "shot_02" in filename:
                if not check_face_morphing(filename):
                    print("  [Pipeline] QA failed, returning False to trigger retry")
                    return False
            return True
        if status == 'failed':
            raise Exception("Video failed")
        time.sleep(15)

print(">> Generating Image 1...")
img1 = fetch_json("https://apihub.agnes-ai.com/v1/images/generations", {
    "model": "agnes-image-2.1-flash",
    "prompt": "A cinematic shot inside a dimly lit modern laboratory at night. Piles of academic papers are stacked on the desk. A middle-aged man in a suit arrogantly picks up a hard drive from the desk, smirking. A young woman with glasses looks up at him with a shocked and angry expression. Dramatic cold lighting, highly detailed, 8k resolution. --seed 10245 --quality highly_detailed, consistent_face",
    "size": "1024x768",
    "extra_body": {"response_format": "url"}
})
img_url1 = img1['data'][0]['url']
download(img_url1, f"{ASSETS_DIR}/shot_01.png")

print(">> Generating Video 1...")
vid1 = fetch_json("https://apihub.agnes-ai.com/v1/videos", {
    "model": "agnes-video-v2.0",
    "prompt": "The man grabs the drive slowly. Camera pans.",
    "first_frame": img_url1,
    "last_frame": img_url1,
    "num_frames": 121,
    "frame_rate": 24
})
task1 = vid1.get('video_id') or vid1.get('task_id')

print(">> Generating Image 2...")
img2 = fetch_json("https://apihub.agnes-ai.com/v1/images/generations", {
    "model": "agnes-image-2.1-flash",
    "prompt": "A bright, high-end corporate boardroom with large windows. A middle-aged man stands at the podium looking panicked and sweating. A young confident woman walks through the door holding a smartphone displaying a sleek AI interface. A large screen behind them shows a glowing, complex academic knowledge graph. Cinematic lighting, dramatic entrance, highly detailed, photorealistic. --seed 10245 --quality highly_detailed, consistent_face",
    "size": "1024x768",
    "extra_body": {"response_format": "url"}
})
img_url2 = img2['data'][0]['url']
download(img_url2, f"{ASSETS_DIR}/shot_02.png")

print(">> Generating Video 2...")
vid2 = fetch_json("https://apihub.agnes-ai.com/v1/videos", {
    "model": "agnes-video-v2.0",
    "prompt": "The woman walks forward confidently. Slow motion.",
    "first_frame": img_url2,
    "last_frame": img_url2,
    "num_frames": 121,
    "frame_rate": 24
})
task2 = vid2.get('video_id') or vid2.get('task_id')

print(">> Polling Videos...")
poll_video(task1, f"{ASSETS_DIR}/shot_01.mp4")
poll_video(task2, f"{ASSETS_DIR}/shot_02.mp4")

print(">> TTS and Merge...")
subprocess.run(['say', '-v', 'Ting-Ting', '-o', f'{ASSETS_DIR}/shot_01_audio.aiff', '唐导，这个月第四个课题了。代码、数据、论文，我用 Agent 十分钟全搞定，为什么不让我过？'])
subprocess.run(['say', '-v', 'Ting-Ting', '-o', f'{ASSETS_DIR}/shot_02_audio.aiff', '快还有错？！别人还在一行行啃文献，我的 AI 已经跑完了！这都什么时代了，您还在用慢办法？'])

subprocess.run(['ffmpeg', '-y', '-i', f'{ASSETS_DIR}/shot_01.mp4', '-i', f'{ASSETS_DIR}/shot_01_audio.aiff', '-c:v', 'copy', '-c:a', 'aac', '-map', '0:v:0', '-map', '1:a:0', '-shortest', f'{FINAL_DIR}/shot_01_final.mp4'])
subprocess.run(['ffmpeg', '-y', '-i', f'{ASSETS_DIR}/shot_02.mp4', '-i', f'{ASSETS_DIR}/shot_02_audio.aiff', '-c:v', 'copy', '-c:a', 'aac', '-map', '0:v:0', '-map', '1:a:0', '-shortest', f'{FINAL_DIR}/shot_02_final.mp4'])

with open(f'{FINAL_DIR}/concat_list.txt', 'w') as f:
    f.write("file 'shot_01_final.mp4'\nfile 'shot_02_final.mp4'\n")

subprocess.run(['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', f'{FINAL_DIR}/concat_list.txt', '-c', 'copy', f'{FINAL_DIR}/episode-01_master.mp4'])
subprocess.run(['cp', f'{FINAL_DIR}/episode-01_master.mp4', f'{OUT_DIR}/episode-01_master_final.mp4'])

print("DONE!")
