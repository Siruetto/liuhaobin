import json
import pathlib
import sys
import wave


root = pathlib.Path(sys.argv[1])
audio_root = root / "audio"
sections = json.loads(
    (root / "narration_sections.json").read_text(encoding="utf-8")
)

segments = []
for section in sections:
    path = audio_root / ("segment-%02d.wav" % int(section["id"]))
    with wave.open(str(path), "rb") as source:
        params = source.getparams()
        frames = source.readframes(source.getnframes())
        duration = source.getnframes() / float(source.getframerate())
    segments.append(
        {
            "id": section["id"],
            "title": section["title"],
            "target_seconds": section["seconds"],
            "speech_seconds": duration,
            "params": params,
            "frames": frames,
        }
    )

sample_rate = segments[0]["params"].framerate
channels = segments[0]["params"].nchannels
sample_width = segments[0]["params"].sampwidth
total_seconds = sum(item["target_seconds"] for item in segments)
output_frames = []
starts = []
cursor = 0.0

for segment in segments:
    if segment["speech_seconds"] > segment["target_seconds"] + 0.25:
        raise RuntimeError(
            "Segment %s is %.2fs, longer than its %.2fs slot"
            % (
                segment["id"],
                segment["speech_seconds"],
                segment["target_seconds"],
            )
        )
    target_bytes = int(
        segment["target_seconds"] * sample_rate * channels * sample_width
    )
    data = segment["frames"][:target_bytes].ljust(target_bytes, b"\x00")
    output_frames.append(data)
    starts.append(
        {
            "id": segment["id"],
            "title": segment["title"],
            "start": cursor,
            "end": cursor + segment["target_seconds"],
            "speech_seconds": round(segment["speech_seconds"], 3),
        }
    )
    cursor += segment["target_seconds"]

output_path = audio_root / "narration.wav"
with wave.open(str(output_path), "wb") as target:
    target.setnchannels(channels)
    target.setsampwidth(sample_width)
    target.setframerate(sample_rate)
    target.writeframes(b"".join(output_frames))

(root / "narration_timing.json").write_text(
    json.dumps(
        {
            "duration_seconds": total_seconds,
            "sample_rate": sample_rate,
            "channels": channels,
            "sections": starts,
        },
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)
print("Narration: %.1f seconds -> %s" % (cursor, output_path))
