import asyncio
import json
import os
import pathlib
import subprocess
import sys

import edge_tts


root = pathlib.Path(__file__).resolve().parent
audio_root = root / "audio"
audio_root.mkdir(exist_ok=True)
sections = json.loads(
    (root / "narration_sections.json").read_text(encoding="utf-8")
)
ffmpeg = os.environ.get(
    "FFMPEG_EXE", r"C:\Program Files\kedou\ffmpeg.exe"
)


async def generate(section):
    mp3 = audio_root / ("segment-%02d.mp3" % int(section["id"]))
    wav = audio_root / ("segment-%02d.wav" % int(section["id"]))
    communicator = edge_tts.Communicate(
        section["text"],
        voice="zh-CN-XiaoxiaoNeural",
        rate="-4%",
    )
    await communicator.save(str(mp3))
    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-loglevel",
            "error",
            "-i",
            str(mp3),
            "-ar",
            "24000",
            "-ac",
            "1",
            "-c:a",
            "pcm_s16le",
            str(wav),
        ],
        check=True,
    )


async def main():
    for section in sections:
        print("Generating narration section %s" % section["id"])
        await generate(section)


if __name__ == "__main__":
    asyncio.run(main())
    subprocess.run(
        [sys.executable, str(root / "assemble_narration.py"), str(root)],
        check=True,
    )
