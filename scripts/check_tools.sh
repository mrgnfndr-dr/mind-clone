#!/usr/bin/env bash
# Detect optional harvest tools. None are required; the skill degrades gracefully.
# Usage: bash scripts/check_tools.sh
set -u
check() {
  if command -v "$1" >/dev/null 2>&1; then
    echo "OK   $1 ($( "$1" --version 2>/dev/null | head -n1 ))"
  else
    echo "MISS $1 — $2"
  fi
}
echo "== clone: optional tool check =="
check yt-dlp          "install: pip install yt-dlp   (YouTube/podcast captions & audio)"
check whisper         "install: pip install openai-whisper   (ASR for audio without transcripts)"
check ffmpeg          "install via OS package manager   (needed by whisper)"
echo "== built-in WebSearch/WebFetch are always available; text scraping needs no tools =="
