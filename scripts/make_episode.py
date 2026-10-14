#!/usr/bin/env python3
"""Turn an episode script (episodes/YYYY-MM-DD.md) into an MP3 in docs/audio/.

Script lines look like:
    NINA: Goedemorgen!
    MIRTHE: Goeiemorgen, Nina.
Everything else in the file (front matter, headings, sources) is ignored for audio.

Usage: python scripts/make_episode.py episodes/2026-10-15.md
Set FAKE_TTS=1 to use tones instead of real speech (for local testing).
"""
import asyncio
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AUDIO_DIR = ROOT / "docs" / "audio"

# Fixed voices per host (Microsoft neural voices via edge-tts). Fallbacks in order.
VOICES = {
    "NINA": ["nl-NL-FennaNeural", "nl-BE-DenaNeural"],
    "MIRTHE": ["nl-NL-ColetteNeural", "nl-BE-DenaNeural"],
}
# speech rate per host (edge-tts format)
RATES = {"NINA": "+5%", "MIRTHE": "+5%"}
ALIASES = {"MAUD": "NINA", "STERRE": "MIRTHE"}  # older scripts
LINE_RE = re.compile(r"^\s*\**\s*(NINA|MIRTHE|MAUD|STERRE)\s*\**\s*:\s*(.+?)\s*$", re.IGNORECASE)


def parse_lines(text: str):
    lines = []
    for raw in text.splitlines():
        m = LINE_RE.match(raw)
        if m:
            speaker = m.group(1).upper()
            speaker = ALIASES.get(speaker, speaker)
            # strip markdown emphasis and stage directions in (brackets) or [brackets]
            said = re.sub(r"[\*_`]", "", m.group(2))
            said = re.sub(r"\([^)]*\)|\[[^\]]*\]", "", said)
            said = re.sub(r"\s+", " ", said).strip()
            if said:
                lines.append((speaker, said))
    return lines


async def tts_line(text: str, speaker: str, out: Path):
    if os.environ.get("FAKE_TTS") == "1":
        freq = 440 if speaker == "NINA" else 660
        dur = max(0.5, len(text) / 15)  # rough speaking time
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i",
                        f"sine=frequency={freq}:duration={dur}", "-ar", "24000", "-ac", "1",
                        str(out)], check=True)
        return
    import edge_tts
    last_err = None
    for voice in VOICES[speaker]:
        for attempt in range(3):
            try:
                await edge_tts.Communicate(text, voice, rate=RATES[speaker]).save(str(out))
                if out.exists() and out.stat().st_size > 0:
                    return
            except Exception as e:  # network hiccup or voice missing
                last_err = e
                await asyncio.sleep(2 * (attempt + 1))
    raise RuntimeError(f"TTS failed for {speaker}: {last_err}")


async def build(script_path: Path) -> Path:
    lines = parse_lines(script_path.read_text(encoding="utf-8"))
    if not lines:
        sys.exit(f"No NINA:/MIRTHE: lines found in {script_path}")
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    out_mp3 = AUDIO_DIR / (script_path.stem + ".mp3")

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        # short pause between speakers, slightly longer pause on speaker change feels natural
        pause = tmp / "pause.mp3"
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i",
                        "anullsrc=r=24000:cl=mono", "-t", "0.35", str(pause)], check=True)
        parts = []
        for i, (speaker, said) in enumerate(lines):
            seg = tmp / f"{i:04d}.mp3"
            await tts_line(said, speaker, seg)
            parts.append(seg)
            parts.append(pause)
        listfile = tmp / "list.txt"
        listfile.write_text("".join(f"file '{p}'\n" for p in parts))
        # re-encode to one consistent mono MP3, loudness-normalised for the car
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0",
                        "-i", str(listfile), "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
                        "-ar", "44100", "-ac", "1", "-b:a", "64k", str(out_mp3)], check=True)
    print(f"Wrote {out_mp3} ({len(lines)} lines)")
    return out_mp3


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    asyncio.run(build(Path(sys.argv[1])))
