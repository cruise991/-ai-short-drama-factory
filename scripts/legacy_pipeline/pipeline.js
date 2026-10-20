const fs = require('fs');
const { execSync } = require('child_process');

const API_KEY = process.env.AGNES_API_KEY || """";
const ASSETS_DIR = "projects/paperai-series/episode-01/02_raw_assets";
const FINAL_DIR = "projects/paperai-series/episode-01/04_final_output";
const OUT_DIR = "../out";

fs.mkdirSync(ASSETS_DIR, { recursive: true });
fs.mkdirSync(FINAL_DIR, { recursive: true });
fs.mkdirSync(OUT_DIR, { recursive: true });

async function fetchJSON(url, body) {
    const res = await fetch(url, {
        method: body ? 'POST' : 'GET',
        headers: {
            'Authorization': `Bearer ${API_KEY}`,
            'Content-Type': 'application/json'
        },
        body: body ? JSON.stringify(body) : undefined
    });
    const text = await res.text();
    try {
        return JSON.parse(text);
    } catch(e) {
        console.error("Failed to parse JSON:", text);
        throw e;
    }
}

async function download(url, filename) {
    console.log(`Downloading ${url} to ${filename}...`);
    const res = await fetch(url);
    if (!res.ok) throw new Error(`unexpected response ${res.statusText}`);
    const buffer = await res.arrayBuffer();
    fs.writeFileSync(filename, Buffer.from(buffer));
    console.log(`Downloaded ${filename}`);
}

async function pollVideo(taskId, filename) {
    while (true) {
        const res = await fetchJSON(`https://apihub.agnes-ai.com/agnesapi?video_id=${taskId}&model_name=agnes-video-2.5-flash`);
        console.log(`Task ${taskId} status: ${res.status}`);
        if (res.status === 'completed') {
            const vidUrl = res.url || res.remixed_from_video_id;
            await download(vidUrl, filename);
            return;
        }
        if (res.status === 'failed') throw new Error(`Task ${taskId} failed`);
        await new Promise(r => setTimeout(r, 15000));
    }
}

async function run() {
    console.log(">> Generating Image 1...");
    const img1 = await fetchJSON("https://apihub.agnes-ai.com/v1/images/generations", {
        "model": "agnes-image-2.5-flash",
        "prompt": "A cinematic shot inside a dimly lit modern laboratory at night. Piles of academic papers are stacked on the desk. A middle-aged man in a suit arrogantly picks up a hard drive from the desk, smirking. A young woman with glasses looks up at him with a shocked and angry expression. Dramatic cold lighting, highly detailed, 8k resolution. --seed 10245 --quality highly_detailed, consistent_face",
        "size": "2K",
        "ratio": "16:9",
        "extra_body": {"response_format": "url"}
    });
    const imgUrl1 = img1.data[0].url;
    await download(imgUrl1, `${ASSETS_DIR}/shot_01.png`);

    console.log(">> Generating Video 1...");
    const vid1 = await fetchJSON("https://apihub.agnes-ai.com/v1/videos", {
        "model": "agnes-video-2.5-flash",
        "prompt": "The man grabs the drive slowly. Camera pans.",
        "mode": "keyframe",
        "first_frame": imgUrl1,
        "seconds": "5",
        "size": "720P",
        "aspect_ratio": "16:9"
    });
    const taskId1 = vid1.video_id || vid1.task_id;

    console.log(">> Generating Image 2...");
    const img2 = await fetchJSON("https://apihub.agnes-ai.com/v1/images/generations", {
        "model": "agnes-image-2.5-flash",
        "prompt": "A bright, high-end corporate boardroom with large windows. A middle-aged man stands at the podium looking panicked and sweating. A young confident woman walks through the door holding a smartphone displaying a sleek AI interface. A large screen behind them shows a glowing, complex academic knowledge graph. Cinematic lighting, dramatic entrance, highly detailed, photorealistic. --seed 10245 --quality highly_detailed, consistent_face",
        "size": "2K",
        "ratio": "16:9",
        "extra_body": {"response_format": "url"}
    });
    const imgUrl2 = img2.data[0].url;
    await download(imgUrl2, `${ASSETS_DIR}/shot_02.png`);

    console.log(">> Generating Video 2...");
    const vid2 = await fetchJSON("https://apihub.agnes-ai.com/v1/videos", {
        "model": "agnes-video-2.5-flash",
        "prompt": "The woman walks forward confidently. Slow motion.",
        "mode": "keyframe",
        "first_frame": imgUrl2,
        "seconds": "5",
        "size": "720P",
        "aspect_ratio": "16:9"
    });
    const taskId2 = vid2.video_id || vid2.task_id;

    console.log(">> Polling Videos...");
    await Promise.all([
        pollVideo(taskId1, `${ASSETS_DIR}/shot_01.mp4`),
        pollVideo(taskId2, `${ASSETS_DIR}/shot_02.mp4`)
    ]);

    console.log(">> Running TTS...");
    execSync(`say -v Ting-Ting -o "${ASSETS_DIR}/shot_01_audio.aiff" "唐导，这个月第四个课题了。代码、数据、论文，我用 Agent 十分钟全搞定，为什么不让我过？"`);
    execSync(`say -v Ting-Ting -o "${ASSETS_DIR}/shot_02_audio.aiff" "快还有错？！别人还在一行行啃文献，我的 AI 已经跑完了！这都什么时代了，您还在用慢办法？"`);

    console.log(">> FFmpeg merging...");
    execSync(`ffmpeg -y -i "${ASSETS_DIR}/shot_01.mp4" -i "${ASSETS_DIR}/shot_01_audio.aiff" -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 -shortest "${FINAL_DIR}/shot_01_final.mp4" </dev/null`);
    execSync(`ffmpeg -y -i "${ASSETS_DIR}/shot_02.mp4" -i "${ASSETS_DIR}/shot_02_audio.aiff" -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 -shortest "${FINAL_DIR}/shot_02_final.mp4" </dev/null`);

    console.log(">> Concat...");
    fs.writeFileSync(`${FINAL_DIR}/concat_list.txt`, "file 'shot_01_final.mp4'\nfile 'shot_02_final.mp4'\n");
    execSync(`ffmpeg -y -f concat -safe 0 -i "${FINAL_DIR}/concat_list.txt" -c copy "${FINAL_DIR}/episode-01_master.mp4" </dev/null`);
    
    fs.copyFileSync(`${FINAL_DIR}/episode-01_master.mp4`, `${OUT_DIR}/episode-01_master_final.mp4`);
    console.log("DONE!");
}

run().catch(console.error);
