const fs = require('fs');

async function download(url, filename) {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`unexpected response ${res.statusText}`);
    const buffer = await res.arrayBuffer();
    fs.writeFileSync(filename, Buffer.from(buffer));
    console.log(`Downloaded ${filename}`);
}

async function run() {
    await download('https://platform-outputs.agnes-ai.space/images/t2i/68a0fba5a860403d89bb63a1d858fdfb.png', 'projects/paperai-series/episode-01/02_raw_assets/shot_01.png');
    // I also need image 2 and videos!
}
run().catch(console.error);
