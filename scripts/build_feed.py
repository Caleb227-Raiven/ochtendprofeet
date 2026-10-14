#!/usr/bin/env python3
"""Build docs/feed.xml (podcast RSS) from docs/audio/*.mp3 and episodes/*.md.

Keeps the newest KEEP episodes; older MP3s are deleted to keep the repo small.
Base URL comes from GITHUB_REPOSITORY (owner/repo) -> https://owner.github.io/repo/
or from the PODCAST_BASE_URL environment variable.
"""
import json
import os
import subprocess
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
AUDIO_DIR = ROOT / "docs" / "audio"
EPISODES_DIR = ROOT / "episodes"
KEEP = 30

SHOW_TITLE = "De Ochtendprofeet"
SHOW_DESC = ("Elke werkdag een gesprek van maximaal 20 minuten over AI, marketing-technologie, "
             "data, CRM en softwareontwikkeling, met Nina en Mirthe.")


def base_url() -> str:
    if os.environ.get("PODCAST_BASE_URL"):
        return os.environ["PODCAST_BASE_URL"].rstrip("/") + "/"
    owner, repo = os.environ.get("GITHUB_REPOSITORY", "owner/repo").split("/")
    return f"https://{owner.lower()}.github.io/{repo}/"


def front_matter(md: Path) -> dict:
    meta = {}
    if not md.exists():
        return meta
    lines = md.read_text(encoding="utf-8").splitlines()
    if lines and lines[0].strip() == "---":
        for line in lines[1:]:
            if line.strip() == "---":
                break
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip().lower()] = v.strip().strip('"')
    return meta


def duration_seconds(mp3: Path) -> int:
    try:
        out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                              "-of", "json", str(mp3)], capture_output=True, text=True, check=True)
        return int(float(json.loads(out.stdout)["format"]["duration"]))
    except Exception:
        return 0


def main():
    base = base_url()
    mp3s = sorted(AUDIO_DIR.glob("*.mp3"), reverse=True)
    for old in mp3s[KEEP:]:
        old.unlink()
    mp3s = mp3s[:KEEP]

    items = []
    for mp3 in mp3s:
        date = datetime.strptime(mp3.stem, "%Y-%m-%d").replace(hour=6, tzinfo=timezone.utc)
        meta = front_matter(EPISODES_DIR / f"{mp3.stem}.md")
        title = meta.get("title") or f"Aflevering {mp3.stem}"
        summary = meta.get("summary") or ""
        secs = duration_seconds(mp3)
        url = f"{base}audio/{mp3.name}"
        items.append(f"""    <item>
      <title>{escape(title)}</title>
      <description>{escape(summary)}</description>
      <itunes:summary>{escape(summary)}</itunes:summary>
      <enclosure url="{url}" length="{mp3.stat().st_size}" type="audio/mpeg"/>
      <guid isPermaLink="false">{mp3.stem}</guid>
      <pubDate>{format_datetime(date)}</pubDate>
      <itunes:duration>{secs}</itunes:duration>
      <itunes:explicit>false</itunes:explicit>
    </item>""")

    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
  <channel>
    <title>{SHOW_TITLE}</title>
    <link>{base}</link>
    <language>nl</language>
    <description>{escape(SHOW_DESC)}</description>
    <itunes:summary>{escape(SHOW_DESC)}</itunes:summary>
    <itunes:author>{SHOW_TITLE}</itunes:author>
    <itunes:image href="{base}cover.png"/>
    <itunes:category text="Technology"/>
    <itunes:type>episodic</itunes:type>
    <itunes:explicit>false</itunes:explicit>
{chr(10).join(items)}
  </channel>
</rss>
"""
    (ROOT / "docs" / "feed.xml").write_text(feed, encoding="utf-8")
    print(f"Feed: {base}feed.xml ({len(items)} episodes)")


if __name__ == "__main__":
    main()
