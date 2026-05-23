# ElevenLabs Skills

Claude Code 와 Codex CLI 에서 사용할 수 있는 ElevenLabs 개발자 스킬 모음입니다. 현재는 Scribe v2 기반 음성→텍스트 전사 스킬이 포함되어 있습니다.

## 포함된 스킬

- `elevenlabs-toolkit:speech-to-text` — 오디오/비디오 파일을 텍스트로 전사 (Scribe v2).
  - Python CLI `transcribe.py` 단일 파일 제공
  - 결정 트리: `.env` 점검 → 파일 길이 사전 측정 → 긴 파일은 샘플 테스트 권유 → 자동 저장 (`<음성파일명>_<날짜시간>.<확장자>`)
  - 90+ 언어 자동 감지, 화자 구분, 단어별 타임스탬프, SRT 자막 출력 지원

## 설치

**Claude Code:**

```bash
claude plugin marketplace add hanlimspeedy/elevenlabs-api
claude plugin install elevenlabs-toolkit@elevenlabs-skills
```

**Codex:**

```bash
codex plugin marketplace add hanlimspeedy/elevenlabs-api --ref main
```

Codex 는 그 후 `/plugins` 메뉴에서 `ElevenLabs Skills > elevenlabs-toolkit` 를 설치하고 새 thread 를 시작합니다.

## 사용

스킬 이름을 직접 호명하는 것이 가장 안정적입니다.

```text
speech-to-text 스킬로 meeting.m4a 전사해줘
```

또는 작업을 그냥 묘사해도 Claude/Codex 가 SKILL.md 의 description 을 보고 매칭해줍니다.

```text
이 회의 녹음 텍스트로 옮겨줘
이 영상에서 자막 파일 만들어줘
```

## 업데이트

### 사용자 쪽 (스킬을 받은 사람)

**Claude Code:**

```bash
claude plugin marketplace update elevenlabs-skills
```

**Codex:**

```bash
codex plugin marketplace upgrade elevenlabs-skills
```

업데이트 후에는 새 세션 또는 새 thread 를 시작해야 변경 사항이 반영됩니다.

> **업데이트 감지는 자동입니다.** 마켓플레이스 명령이 매니페스트의 `version` 필드를 비교해 갱신을 결정합니다. 사용자가 따로 체크 문서를 보거나 수동으로 비교할 필요 없습니다.

### 메인테이너 쪽 (이 저장소를 수정하는 사람)

스킬, 템플릿, 문서를 바꿨다면 **반드시 4개 매니페스트의 `version` 을 동일하게 올려서** 커밋합니다. 안 올리면 사용자 쪽 마켓플레이스가 "이미 최신" 으로 판단해서 변경을 받지 못합니다.

| 파일 | 비고 |
|------|------|
| `.claude-plugin/marketplace.json` | `metadata.version` 필드 |
| `.agents/plugins/marketplace.json` | 버전 필드 없음 (카탈로그용) |
| `plugins/elevenlabs-toolkit/.claude-plugin/plugin.json` | `version` 필드 |
| `plugins/elevenlabs-toolkit/.codex-plugin/plugin.json` | `version` 필드 |

버전 규칙 (Semantic Versioning):

- **패치** (`0.1.0` → `0.1.1`): 버그 수정, 문서 수정, 메시지 변경 등
- **마이너** (`0.1.0` → `0.2.0`): 새 옵션/기능 추가, 하위 호환 유지
- **메이저** (`0.1.0` → `1.0.0`): 깨지는 변경 (CLI 인자 제거, 동작 방식 변경 등)

## 검증

JSON 매니페스트 4개 모두 유효한지 확인:

```bash
jq . .claude-plugin/marketplace.json
jq . .agents/plugins/marketplace.json
jq . plugins/elevenlabs-toolkit/.claude-plugin/plugin.json
jq . plugins/elevenlabs-toolkit/.codex-plugin/plugin.json
```

Claude Code 플러그인 추가 검증 (선택):

```bash
claude plugin validate plugins/elevenlabs-toolkit
```

Codex 는 별도 validate 명령이 없으니 marketplace 명령으로 동작 확인합니다:

```bash
codex plugin marketplace add hanlimspeedy/elevenlabs-api --ref main
codex plugin marketplace upgrade elevenlabs-skills
```

## 디렉토리 구조

```text
.claude-plugin/marketplace.json                         # Claude 마켓플레이스 카탈로그
.agents/plugins/marketplace.json                        # Codex 마켓플레이스 카탈로그
.claude/skills/speech-to-text -> ../../plugins/elevenlabs-toolkit/skills/speech-to-text   # 개발용 심볼릭
.agents/skills/speech-to-text -> ../../plugins/elevenlabs-toolkit/skills/speech-to-text   # 개발용 심볼릭
plugins/elevenlabs-toolkit/
  .claude-plugin/plugin.json                            # Claude 플러그인 매니페스트 (버전 보유)
  .codex-plugin/plugin.json                             # Codex 플러그인 매니페스트 (버전 보유)
  skills/
    speech-to-text/                                     # ← 스킬 본체 (수정은 여기서만)
      SKILL.md
      templates/
        transcribe.py
        requirements.txt
        .env.example
      references/
        transcription-options.md
```

상단의 두 심볼릭 (`.claude/skills/`, `.agents/skills/`) 은 **이 저장소 안에서 직접 개발할 때** Claude Code 와 Codex 가 스킬을 찾을 수 있도록 만든 편의용입니다. 외부 사용자는 마켓플레이스로 설치하므로 이 심볼릭에 접근하지 않습니다.

**스킬 내용 수정은 반드시 `plugins/elevenlabs-toolkit/skills/speech-to-text/` 에서만 합니다.** 두 심볼릭은 모두 이 경로를 가리킵니다.

## 스탠드얼론 사용 (플러그인 설치 없이)

저장소 루트의 `transcribe.py` 는 그 자체로 동작하는 CLI 입니다. 스킬 설치 없이도 바로 사용 가능:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env             # .env 를 열어 ELEVENLABS_API_KEY 값을 채우기
.venv/bin/python transcribe.py audio.m4a
```

API 키 발급: https://elevenlabs.io/app/developers/api-keys

자주 쓰는 옵션:

```bash
# 화자 구분
.venv/bin/python transcribe.py meeting.m4a --diarize

# SRT 자막 생성
.venv/bin/python transcribe.py video.mp4 --format srt

# 전체 JSON (타임스탬프 + 화자)
.venv/bin/python transcribe.py call.m4a --diarize --timestamps --format json

# 한국어 힌트 + 키텀
.venv/bin/python transcribe.py ko.m4a -l kor -k "엘레븐랩스" "스크라이브"

# 저장 안 하고 stdout 으로만
.venv/bin/python transcribe.py audio.m4a --stdout
```

저장 파일명 규칙: `-o` 옵션을 안 주면 `<음성파일명>_<YYYY-MM-DD_HHMM>.<ext>` 형식으로 원본 옆에 자동 저장됩니다.

## 라이선스

MIT
