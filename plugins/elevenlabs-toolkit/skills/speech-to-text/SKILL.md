---
name: speech-to-text
description: Transcribe audio/video to text using ElevenLabs Scribe v2. Use when the user asks to transcribe a recording, generate subtitles, extract text from audio/video, or get a transcript of speech in any of 90+ languages.
license: MIT
compatibility: Requires internet access and an ElevenLabs API key (ELEVENLABS_API_KEY).
metadata: {"openclaw": {"requires": {"env": ["ELEVENLABS_API_KEY"]}, "primaryEnv": "ELEVENLABS_API_KEY"}}
---

# ElevenLabs Speech-to-Text (Custom)

When this skill triggers, you (Claude) **must** follow the decision tree below in order. Do not skip steps. Do not invent transcription code on your own when a working CLI already exists in the project.

---

## Decision tree

### Step 0 — Prerequisites: 스킬 실행 시마다 확인

스킬이 트리거되면 **매 실행마다** 아래 도구들을 확인합니다. 도구 없이 무시하고 진행하지 마세요. 단 정책이 도구별로 다릅니다 — 잘 읽고 따르세요.

**0-1. Python 3 + venv + pip (필수, 없으면 진행 불가)**

```bash
python3 --version >/dev/null 2>&1 && \
python3 -m venv --help >/dev/null 2>&1 && \
python3 -m pip --version >/dev/null 2>&1 && echo OK || echo NEEDS_PYTHON
```

`NEEDS_PYTHON` 이면 사용자에게 설치 안내:

| OS | 명령 |
|----|------|
| macOS (Homebrew) | `brew install python3` |
| Ubuntu/Debian | `sudo apt install -y python3 python3-venv python3-pip` |
| Fedora/RHEL | `sudo dnf install -y python3 python3-pip` |
| Windows | `winget install Python.Python.3.12` |

> 함정: Debian/Ubuntu 는 `python3` 만 있고 `python3-venv` 패키지가 없을 수 있습니다. 위 명령은 3개 패키지를 한 번에 설치합니다.

Python 은 전사 자체에 필요하므로 설치 없이는 진행 불가. 사용자가 설치 명령을 실행할 때까지 다음 단계로 가지 마세요.

**0-2. ffmpeg / ffprobe (없어도 진행은 가능, 단 매번 묻기)**

```bash
which ffprobe >/dev/null 2>&1 && which ffmpeg >/dev/null 2>&1 && echo OK || echo NEEDS_FFMPEG
```

`NEEDS_FFMPEG` 면 **매 실행마다** 사용자에게 묻습니다 (캐시 금지, 이전 응답 재사용 금지). 한국어 예시:

> ⚠️ ffmpeg 가 설치되어 있지 않습니다.
> ffmpeg 가 있어야 **파일 길이 측정**과 **샘플 테스트 (앞 2분 잘라 미리 보기)** 가 가능합니다.
> 어떻게 할까요?
>
> 1. **설치** (권장) — OS 별 명령 안내해 드립니다
> 2. **설치 없이 그대로 진행** — 길이 측정과 샘플 테스트 없이 입력 파일을 통째로 전사 (긴 파일이면 시간·크레딧 위험)

| OS | 설치 명령 |
|----|----------|
| macOS (Homebrew) | `brew install ffmpeg` |
| Ubuntu/Debian | `sudo apt install -y ffmpeg` |
| Fedora/RHEL | `sudo dnf install -y ffmpeg` |
| Windows | `winget install ffmpeg` (또는 `choco install ffmpeg`) |

- **1 선택** → 설치 후 다시 0-2 검사. OK 가 나오면 Step 1.
- **2 선택** → 사용자가 명시적으로 위험 감수. Step 4 의 사전 점검을 건너뛰고 바로 전체 전사. 단, 진행 직전에 한 번 더 "정말 길이 측정 없이 전체 파일을 전사할까요?" 확인.
- **응답 없음/모호함** → 1 (설치) 로 처리. 절대 침묵으로 2 를 선택하지 마세요.

> ⚠️ **AI 가 자주 저지르는 실수**: ffmpeg 가 없으면 "어차피 못 하니까 그냥 통째로 전사하자" 라고 사용자에게 묻지도 않고 진행하는 것. 금지. 매번 위 질문을 사용자에게 던지세요.

### Step 1 — Check .env (API 키)

```bash
grep -q '^ELEVENLABS_API_KEY=sk_' .env 2>/dev/null && echo OK || echo NEEDS_KEY
```

- **OK** → proceed to Step 2
- **NEEDS_KEY** → guide the user (in Korean):
  1. `.env` 파일이 없거나 키가 없으면 먼저 만듭니다:
     ```bash
     test -f .env || cp .claude/skills/speech-to-text/templates/.env.example .env
     # .env.example 이 프로젝트 루트에 있으면: cp .env.example .env
     ```
  2. 사용자에게 안내: "https://elevenlabs.io/app/developers/api-keys 에서 키를 발급받아 `.env` 파일의 `ELEVENLABS_API_KEY=` 뒤에 붙여넣고 저장해 주세요."
  3. 사용자가 저장했다고 알려주면 위 grep 명령으로 다시 확인 후 진행.

  Claude **must not** generate, guess, or fabricate an API key.

### Step 2 — Detect existing CLI in the project

Check whether `transcribe.py` exists at the **project root** (the user's current working directory, not the skill folder):

```bash
test -f ./transcribe.py && echo "FOUND" || echo "MISSING"
```

- **FOUND** → go to **Mode A: Use existing code**
- **MISSING** → go to **Step 3**

### Step 3 — Ask the user which mode to use

Ask the user (in their language) exactly this choice — do **not** decide for them:

> 프로젝트에 전사 코드가 없습니다. 어떻게 진행할까요?
> 1. **코드 생성** — 스킬 템플릿에서 `transcribe.py` 를 복사하고 venv + 의존성을 자동 설치 (재사용 가능, 빠름)
> 2. **공식 md 기반** — ElevenLabs 공식 문서를 참조해 SDK 호출 코드를 즉석에서 작성 (1회용)

- Option 1 → go to **Mode B: Generate code from template**
- Option 2 → go to **Mode C: Inline md-based call**

### Step 4 — Pre-flight: 입력 파일 길이 점검 (실행 직전에 항상)

Mode A/B/C 어느 경로든 실제 전사 호출 **직전에** 반드시 수행합니다. 1시간짜리 파일을 그대로 던졌다가 실패하면 시간·크레딧만 낭비됩니다.

> Step 0-2 에서 ffmpeg "설치 없이 그대로 진행" 을 사용자가 선택했다면 이 Step 4 전체를 건너뛰고 바로 원본 전체 전사로 갑니다.

**4-0. 🚨 샘플 파일 재사용 금지 (극상 우선순위)**

작업 디렉토리에 `<원본명>_sample_*s.<ext>` 오디오나 `*_sample_*s_*.txt` 전사가 이미 존재해도 **절대로 "이전에 이미 했네, 그냥 전체 가자" 라고 결정하지 마세요.** 이전 실행에서 다음 중 하나일 수 있습니다:

- 사용자가 결과를 보고 **불만족** 했지만 응답 없이 떠난 상태
- 샘플 전사 자체가 **실패**해서 부분 결과만 남은 상태
- 사용자가 명시적으로 **중단**했는데 파일만 남은 상태
- 다른 시점의 시도이고 사용자가 잊은 상태

따라서 규칙:

1. 매 스킬 실행마다 4-3 의 사용자 질문을 **반드시 새로 던진다**. 디스크에 파일 있다고 건너뛰지 않는다.
2. 기존 샘플 파일을 발견하면 사용자에게 정확히 이렇게 알린다:
   > 📁 이전에 만든 샘플 파일이 발견됐습니다: `<경로>`
   > 직전 시도가 끝까지 성공했는지 알 수 없으니, 한 번 더 확인하겠습니다.
3. 그 다음 정상적으로 4-3 의 "샘플 / 전체 / 무시" 질문 진행. 사용자가 "이전 결과로 충분" 이라고 명시하면 그때 전체로 진행.
4. 같은 파일에 대한 **반복 실행도 동일 규칙** — 캐싱 금지, 자동 결정 금지.

> AI 가 자주 저지르는 극상급 실수: "파일 있네 → 이전에 성공한 거겠지 → 전체 47분짜리 전사 실행" → 사용자 크레딧 다 날아감.

**4-1. 길이 측정**

```bash
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "<audio-file>"
```

초 단위 실수가 나옵니다. 분/초로 환산해 사용자에게 표시 (예: `2877.05초 → 47분 57초`).

**4-2. 길이 기반 분기**

| 길이 | 동작 |
|------|------|
| < 60초 | 묻지 않고 바로 전체 실행 |
| 60초 ~ 10분 | 사용자에게 한 번 묻기 (샘플 vs 전체) |
| > 10분 | **강력히** 샘플 권장하며 묻기 (무료 사용자는 특히) |

**4-3. 사용자에게 묻는 형식 (한국어)**

> 📊 입력 파일: **X분 Y초**
>
> 길이가 있어 전체 실행 시 시간이 걸리고, 도중에 실패하면 크레딧이 소진될 수 있습니다.
> 1. **샘플 테스트** — 앞 2분만 잘라 먼저 전사해보고 결과 확인 후 전체 진행 (앞부분에 묵음이 많을 수 있어 30초로는 부족)
> 2. **전체 실행** — 그냥 전체를 바로 전사
>
> (응답 없거나 "무시"/"그냥 진행" 이면 2번)

**4-4. 샘플 테스트 선택 시 흐름**

샘플 파일을 **원본과 같은 폴더에 의미 있는 이름으로** 저장합니다 (`/tmp` 에 두지 마세요). 그래야 자동 생성되는 전사 파일명에도 `_sample_120s_` 가 들어가 한눈에 구분됩니다.

```bash
# 입력이 meeting.m4a 일 때: meeting_sample_120s.m4a 생성
# (확장자/디렉토리는 원본을 따른다. 120 은 실제 사용한 초 수와 일치시킬 것)
INPUT="<원본경로>"           # 예: meeting.m4a
SEC=120
STEM="${INPUT%.*}"
EXT="${INPUT##*.}"
SAMPLE="${STEM}_sample_${SEC}s.${EXT}"
ffmpeg -y -i "$INPUT" -ss 0 -t "$SEC" -c copy "$SAMPLE" 2>/dev/null
```

1. `$SAMPLE` 로 전사 실행. **샘플은 반드시 `--diarize` 를 켜서** 화자 분리 품질까지 함께 검증합니다 (회의·인터뷰 파일이 대부분이고, 전체 실행 전에 화자 분리가 잘 되는지 확인해야 헛돈을 안 씁니다):
   ```bash
   .venv/bin/python transcribe.py "$SAMPLE" --diarize
   ```
   자동으로 `<stem>_sample_120s_<YYYY-MM-DD_HHMM>.txt` 로 저장되며, `[speaker_0] ...` 형식의 화자 라벨이 포함됩니다.
2. 결과 파일 경로와 내용 일부(특히 화자 라벨 흐름)를 사용자에게 보여주기
3. 사용자에게 다시 묻기: "샘플 결과 OK 면 전체 파일을 전사할까요? 화자 분리도 그대로 적용할까요?"
4. 진행 응답이면 원본 파일로 동일 옵션(`--diarize`) 으로 실행 (자동 저장됨). 사용자가 화자 분리가 불필요하다고 하면 옵션 빼고 실행.

**4-5. 전체 실행 선택 시 (또는 응답 없음)**

바로 원본 파일로 전사 실행.

---

## Mode A — Use existing code (preferred)

1. Verify dependencies are installed. Check for venv and the `elevenlabs` package:
   ```bash
   test -d .venv && .venv/bin/python -c "import elevenlabs" 2>/dev/null && echo OK || echo NEEDS_INSTALL
   ```
   If `NEEDS_INSTALL`, run:
   ```bash
   python3 -m venv .venv
   .venv/bin/pip install -q -r requirements.txt
   ```

2. Run the CLI directly. Common invocations:
   ```bash
   # Basic
   .venv/bin/python transcribe.py <audio-file>

   # Save to file
   .venv/bin/python transcribe.py <audio-file> -o out.txt

   # Speaker diarization
   .venv/bin/python transcribe.py <audio-file> --diarize -o meeting.txt

   # Subtitles (SRT)
   .venv/bin/python transcribe.py <audio-file> --format srt -o subs.srt

   # Full JSON (timestamps + speakers)
   .venv/bin/python transcribe.py <audio-file> --diarize --timestamps --format json -o out.json

   # Language hint + keyterms
   .venv/bin/python transcribe.py <audio-file> -l kor -k "엘레븐랩스" "스크라이브"
   ```

3. **Do not modify** `transcribe.py` unless the user explicitly asks. Treat it as the canonical implementation.

---

## Mode B — Generate code from template

1. Copy the three template files from this skill to the project root:
   ```bash
   cp .claude/skills/speech-to-text/templates/transcribe.py ./transcribe.py
   cp .claude/skills/speech-to-text/templates/requirements.txt ./requirements.txt
   cp .claude/skills/speech-to-text/templates/.env.example ./.env.example
   ```

2. Set up venv and install dependencies:
   ```bash
   python3 -m venv .venv
   .venv/bin/pip install -q -r requirements.txt
   ```

3. Add `.gitignore` entries if missing (`.env`, `.venv/`).

4. `.env` 점검은 Step 1 에서 이미 처리됨. 키가 있으면 바로 **Mode A** 로 진입해 실행.

---

## Mode C — Inline md-based call (no code file)

Use this only when the user explicitly chose option 2 in Step 3, or when they want a one-off call without creating files.

1. Ensure `ELEVENLABS_API_KEY` is in the environment (from `.env` or shell).

2. Use `pip install --user elevenlabs python-dotenv` or a venv, then write an inline Python invocation. For all available parameters (diarize, timestamps, keyterms, language hints, etc.), see:
   - [Transcription Options](references/transcription-options.md)

3. Minimal one-shot example:
   ```python
   from dotenv import load_dotenv
   from elevenlabs import ElevenLabs
   load_dotenv()
   client = ElevenLabs()
   with open("audio.m4a", "rb") as f:
       r = client.speech_to_text.convert(file=f, model_id="scribe_v2")
   print(r.text)
   ```

4. If the user later wants to reuse the logic, **suggest switching to Mode B** (generate template) so they don't pay the re-typing cost again.

---

## Supported formats (no conversion needed)

- **Audio**: MP3, WAV, M4A, FLAC, OGG, WebM, AAC, AIFF, Opus
- **Video**: MP4, AVI, MKV, MOV, WMV, FLV, WebM, MPEG, 3GPP (audio track auto-extracted)
- **Limits**: 3 GB file size, 10 hours duration
- Convert with ffmpeg only for unsupported formats (AMR, WMA, RA, DRM-protected m4p)

## Models

| Model ID | Description | Best For |
|----------|-------------|----------|
| `scribe_v2` | State-of-the-art accuracy, 90+ languages | Batch transcription, subtitles, long-form audio |
| `scribe_v2_realtime` | Low latency (~150ms) | Live transcription, voice agents |

The CLI defaults to `scribe_v2`. Override with `--model scribe_v2_realtime` for streaming.

---

## What this skill does NOT do

- Real-time microphone streaming → out of scope; this skill is batch file transcription only
- Translation → ElevenLabs STT transcribes only; pipe to a translation step separately
- Speaker enrollment → diarization labels are `speaker_0/1/...`, not named identities

## Free-tier note

무료 사용자는 크레딧이 한정되어 있습니다. Step 4 의 길이 점검에서 사용자가 무료 플랜이라고 알려주면, 10분 미만 파일이어도 샘플 테스트를 더 강하게 권장하세요.
