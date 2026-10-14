#!/usr/bin/env python3
"""Render a short Dutch sample for each candidate voice into docs/samples/.

Also writes docs/samples/voices.txt with every Dutch and multilingual voice edge-tts offers.
"""
import asyncio
from pathlib import Path

import edge_tts

OUT = Path(__file__).resolve().parent.parent / "docs" / "samples"
TEXT = ("Goedemorgen, ik ben Mirthe. Vandaag gaat het over AI-agents in de backoffice. "
        "Klinkt spannend, maar wat betekent het nou echt voor een dealer die gewoon "
        "zijn leads goed wil opvolgen? Nou, daar gaan we het over hebben.")

# (file name, voice, rate, pitch)
CANDIDATES = [
    ("1-colette-huidig", "nl-NL-ColetteNeural", "+5%", "+0Hz"),
    ("2-colette-rustiger", "nl-NL-ColetteNeural", "-3%", "-2Hz"),
    ("3-dena-vlaams", "nl-BE-DenaNeural", "+5%", "+0Hz"),
    ("4-seraphina-meertalig", "de-DE-SeraphinaMultilingualNeural", "+0%", "+0Hz"),
    ("5-vivienne-meertalig", "fr-FR-VivienneMultilingualNeural", "+0%", "+0Hz"),
    ("6-emma-meertalig", "en-US-EmmaMultilingualNeural", "+0%", "+0Hz"),
    ("7-ava-meertalig", "en-US-AvaMultilingualNeural", "+0%", "+0Hz"),
]


async def main():
    OUT.mkdir(parents=True, exist_ok=True)
    voices = await edge_tts.list_voices()
    names = {v["ShortName"] for v in voices}
    listing = sorted(v["ShortName"] + "  " + v.get("Gender", "") for v in voices
                     if v["ShortName"].startswith("nl-") or "Multilingual" in v["ShortName"])
    (OUT / "voices.txt").write_text("\n".join(listing) + "\n")
    for name, voice, rate, pitch in CANDIDATES:
        if voice not in names:
            print(f"skip {voice}: not available")
            continue
        try:
            await edge_tts.Communicate(TEXT, voice, rate=rate, pitch=pitch).save(str(OUT / f"{name}.mp3"))
            print(f"ok {name}")
        except Exception as e:
            print(f"fail {name}: {e}")


if __name__ == "__main__":
    asyncio.run(main())
