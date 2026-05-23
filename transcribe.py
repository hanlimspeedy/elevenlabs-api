#!/usr/bin/env python3
"""ElevenLabs Scribe v2 transcription CLI.

Usage:
    python transcribe.py audio.mp3
    python transcribe.py audio.mp3 -o out.txt
    python transcribe.py call.mp3 --diarize --format srt -o subs.srt
    python transcribe.py meeting.m4a --diarize --timestamps --format json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from elevenlabs import ElevenLabs

AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".flac", ".ogg", ".webm", ".aac", ".aiff", ".opus"}
VIDEO_EXTS = {".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".mpeg", ".3gp", ".3gpp"}


def format_timestamp_srt(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def build_srt(words: list, max_chars: int = 42) -> str:
    """Group words into subtitle lines (~max_chars per line, break on speaker change)."""
    lines = []
    cur_text = ""
    cur_start = None
    cur_end = None
    cur_speaker = None
    idx = 1

    def flush():
        nonlocal cur_text, cur_start, cur_end, idx
        if cur_text.strip():
            lines.append(
                f"{idx}\n{format_timestamp_srt(cur_start)} --> {format_timestamp_srt(cur_end)}\n{cur_text.strip()}\n"
            )
            idx += 1
        cur_text = ""
        cur_start = None
        cur_end = None

    for w in words:
        if w.type != "word":
            if cur_text:
                cur_text += w.text
                cur_end = w.end
            continue
        speaker = getattr(w, "speaker_id", None)
        if cur_start is None:
            cur_start = w.start
            cur_speaker = speaker
        if speaker != cur_speaker or len(cur_text) + len(w.text) > max_chars:
            flush()
            cur_start = w.start
            cur_speaker = speaker
        cur_text += w.text
        cur_end = w.end
    flush()
    return "\n".join(lines)


def format_diarized_text(words: list) -> str:
    """Render diarized transcript as [speaker_X] turn lines."""
    out = []
    cur_speaker = None
    cur_line = ""
    for w in words:
        if w.type != "word" and w.type != "spacing":
            continue
        speaker = getattr(w, "speaker_id", None)
        if speaker != cur_speaker and w.type == "word":
            if cur_line.strip():
                out.append(f"[{cur_speaker}] {cur_line.strip()}")
            cur_speaker = speaker
            cur_line = w.text
        else:
            cur_line += w.text
    if cur_line.strip():
        out.append(f"[{cur_speaker}] {cur_line.strip()}")
    return "\n".join(out)


def transcribe(args: argparse.Namespace) -> int:
    path = Path(args.input)
    if not path.exists():
        print(f"Error: file not found: {path}", file=sys.stderr)
        return 2

    ext = path.suffix.lower()
    if ext not in AUDIO_EXTS and ext not in VIDEO_EXTS:
        print(f"Warning: unrecognized extension {ext}, attempting anyway...", file=sys.stderr)

    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        print("Error: ELEVENLABS_API_KEY not set. Create a .env file or export the variable.", file=sys.stderr)
        return 3

    client = ElevenLabs(api_key=api_key)

    kwargs: dict = {
        "model_id": args.model,
        "diarize": args.diarize,
    }
    if args.language:
        kwargs["language_code"] = args.language
    if args.keyterms:
        kwargs["keyterms"] = args.keyterms
    if args.timestamps or args.format in ("srt", "json"):
        kwargs["timestamps_granularity"] = "word"

    print(f"Transcribing {path.name} (model={args.model}, diarize={args.diarize})...", file=sys.stderr)

    with open(path, "rb") as f:
        result = client.speech_to_text.convert(file=f, **kwargs)

    if args.format == "json":
        output = json.dumps(result.dict() if hasattr(result, "dict") else result, ensure_ascii=False, indent=2, default=str)
    elif args.format == "srt":
        if not getattr(result, "words", None):
            print("Error: SRT format requires word-level timestamps but none returned.", file=sys.stderr)
            return 4
        output = build_srt(result.words)
    else:  # text
        if args.diarize and getattr(result, "words", None):
            output = format_diarized_text(result.words)
        else:
            output = result.text

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Wrote {args.output} ({len(output)} chars)", file=sys.stderr)
    else:
        print(output)

    lang = getattr(result, "language_code", None)
    prob = getattr(result, "language_probability", None)
    if lang:
        print(f"[detected: {lang} {prob:.0%}]" if prob else f"[detected: {lang}]", file=sys.stderr)

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Transcribe audio/video to text using ElevenLabs Scribe v2.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("input", help="Path to audio or video file")
    parser.add_argument("-o", "--output", help="Output file (default: stdout)")
    parser.add_argument(
        "-f", "--format", choices=["text", "json", "srt"], default="text",
        help="Output format (default: text)",
    )
    parser.add_argument("-m", "--model", default="scribe_v2", help="Model ID (default: scribe_v2)")
    parser.add_argument("-l", "--language", help="Language hint, ISO 639 code (e.g. eng, kor)")
    parser.add_argument("-d", "--diarize", action="store_true", help="Enable speaker diarization")
    parser.add_argument("-t", "--timestamps", action="store_true", help="Include word-level timestamps")
    parser.add_argument(
        "-k", "--keyterms", nargs="+",
        help="Keyterms to bias recognition (e.g. product names, jargon)",
    )

    load_dotenv()
    args = parser.parse_args()
    try:
        return transcribe(args)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
