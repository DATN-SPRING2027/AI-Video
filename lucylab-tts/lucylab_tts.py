#!/usr/bin/env python3
"""
LucyLab & TikTok Cloud Vietnamese AI TTS CLI for CreateVideo Studio.
- Primary Cloud Provider (lucylab): https://api.lucylab.io/json-rpc (Docs: https://lucylab.io/docs/api-keys)
  Uses: createProject -> updateProjectBlocks -> exportAudio -> getExportStatus / getProjectExports -> deleteProject
- Automatic Cloud Fallback (tiktok): ByteDance/TikTok Neural Vietnamese TTS via TIKTOK_SESSION_ID
  Voices: BV075_streaming (Male) / BV074_streaming (Female), sentence-chunked & stitched at 48kHz PCM WAV.

Security rule:
- Reads VIETNAMESE_API_KEY, VIETNAMESE_VOICEID_MALE, VIETNAMESE_VOICEID_FEMALE, TIKTOK_SESSION_ID dynamically
  from CreateVideo/.env (or OS environment).
- Never logs, prints, or stores raw API keys or session tokens.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import wave
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent
CREATE_VIDEO_DIR = BASE_DIR.parent
DEFAULT_ENV_FILE = CREATE_VIDEO_DIR / ".env"
LUCYLAB_RPC_URL = "https://api.lucylab.io/json-rpc"
USER_AGENT = "ContinuumVideoPipeline/1.0"

ACTIVE_MALE_FALLBACK_ID = "18wiGQWRzVqJ1G63xncLmq"  # TVC 4 (Active verified Northern Male TVC voice)
PRESET_VOICES: dict[str, str] = {
    "tvc4": "18wiGQWRzVqJ1G63xncLmq",
    "trung-quan": "2LLtWibYKJaiLFeqVkzPGY",
    "quang-anh": "24oEtXGic7NhDjXzmDbDvt",
}

TIKTOK_ENDPOINTS = (
    "https://api16-normal-v6.tiktokv.com/media/api/text/speech/invoke/",
    "https://api16-normal-c-useast1a.tiktokv.com/media/api/text/speech/invoke/",
    "https://api22-normal-c-alisg.tiktokv.com/media/api/text/speech/invoke/",
)
TIKTOK_UA = (
    "com.zhiliaoapp.musically/2022600030 "
    "(Linux; U; Android 7.1.2; es_ES; SM-G988N; Build/NRD90M;tt-ok/3.12.13.1)"
)


class InsufficientCreditsError(RuntimeError):
    """Raised when LucyLab account has 0 / insufficient credits for audio export."""


def load_env_file(env_path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if env_path.exists():
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key:
                values[key] = val
    for key in (
        "VIETNAMESE_API_KEY",
        "VIETNAMESE_VOICEID_MALE",
        "VIETNAMESE_VOICEID_FEMALE",
        "TIKTOK_SESSION_ID",
    ):
        if os.environ.get(key):
            values[key] = os.environ[key].strip()
    return values


def rpc_call(api_key: str, method: str, payload: dict[str, Any], timeout: int = 90) -> Any:
    body = json.dumps({"method": method, "input": payload}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        LUCYLAB_RPC_URL,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        err_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"LucyLab RPC '{method}' HTTP {exc.code}: {err_body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"LucyLab RPC '{method}' connection error: {exc.reason}") from exc

    parsed = json.loads(raw)
    if isinstance(parsed, dict) and parsed.get("error"):
        err = parsed["error"]
        err_data = err.get("data") if isinstance(err, dict) else None
        if isinstance(err_data, dict) and err_data.get("code") == "insufficient_credits":
            raise InsufficientCreditsError(
                f"LucyLab hết credit (required={err_data.get('required')}, available={err_data.get('available')}): "
                f"{err.get('message')}"
            )
        raise RuntimeError(f"LucyLab RPC '{method}' error: {err}")
    return parsed.get("result", parsed)


def resolve_lucylab_voice(api_key: str, voice_arg: str, env: dict[str, str]) -> tuple[str, str]:
    alias = voice_arg.strip().lower()
    is_male_alias = alias in ("male", "nam", "default", "")
    if is_male_alias:
        candidate = env.get("VIETNAMESE_VOICEID_MALE", "").strip() or ACTIVE_MALE_FALLBACK_ID
    elif alias in ("female", "nu", "nữ"):
        candidate = env.get("VIETNAMESE_VOICEID_FEMALE", "").strip()
        if not candidate:
            raise ValueError("Missing VIETNAMESE_VOICEID_FEMALE in CreateVideo/.env")
    elif alias in PRESET_VOICES:
        candidate = PRESET_VOICES[alias]
    else:
        candidate = voice_arg.strip()

    voices = rpc_call(api_key, "getUserVoicesByIds", {"ids": [candidate]})
    if isinstance(voices, list) and voices:
        v = voices[0]
        v_name = str(v.get("name") or candidate)
        if v.get("isActive", True):
            return candidate, v_name
        if is_male_alias and candidate != ACTIVE_MALE_FALLBACK_ID:
            fb_list = rpc_call(api_key, "getUserVoicesByIds", {"ids": [ACTIVE_MALE_FALLBACK_ID]})
            fb_name = str(fb_list[0].get("name")) if fb_list else "TVC 4"
            print(
                f"[LucyLab TTS] Lưu ý: Giọng '{v_name}' ({candidate}) trong .env hiện có isActive=false "
                f"trên máy chủ LucyLab -> Tự động dùng giọng nam TVC đang hoạt động '{fb_name}' ({ACTIVE_MALE_FALLBACK_ID})."
            )
            return ACTIVE_MALE_FALLBACK_ID, fb_name
        raise RuntimeError(
            f"Giọng đọc '{v_name}' ({candidate}) hiện không hoạt động (isActive=false) trên LucyLab."
        )
    return candidate, candidate


def resolve_tiktok_speaker(voice_arg: str) -> str:
    alias = voice_arg.strip().lower()
    if alias in ("female", "nu", "nữ", "bv074", "bv074_streaming"):
        return "BV074_streaming"
    if alias.startswith("bv") and "_streaming" in alias:
        return voice_arg.strip()
    return "BV075_streaming"


def download_file(url: str, dest: Path, timeout: int = 120) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        dest.write_bytes(resp.read())


def convert_audio(src: Path, output_path: Path, sample_rate: int = 48000, speed: float = 1.0) -> Path:
    output_abs = output_path.resolve()
    output_abs.parent.mkdir(parents=True, exist_ok=True)
    ext = output_abs.suffix.lower()

    ffmpeg_bin = shutil.which("ffmpeg")
    if not ffmpeg_bin:
        shutil.copyfile(src, output_abs)
        return output_abs

    af_args: list[str] = []
    if abs(speed - 1.0) > 0.01:
        clamped = max(0.5, min(2.0, speed))
        af_args = ["-filter:a", f"atempo={clamped:.3f}"]

    if ext == ".wav":
        cmd = [
            ffmpeg_bin,
            "-y",
            "-loglevel",
            "error",
            "-i",
            str(src),
            *af_args,
            "-ar",
            str(sample_rate),
            "-ac",
            "1",
            "-c:a",
            "pcm_s16le",
            str(output_abs),
        ]
    elif ext == ".mp3":
        cmd = [
            ffmpeg_bin,
            "-y",
            "-loglevel",
            "error",
            "-i",
            str(src),
            *af_args,
            "-ar",
            str(sample_rate),
            "-c:a",
            "libmp3lame",
            "-b:a",
            "192k",
            str(output_abs),
        ]
    else:
        cmd = [ffmpeg_bin, "-y", "-loglevel", "error", "-i", str(src), *af_args, str(output_abs)]

    subprocess.run(cmd, check=True)
    return output_abs


def _find_export_item(api_key: str, project_id: str, export_id: str) -> dict[str, Any] | None:
    exports_res = rpc_call(
        api_key,
        "getProjectExports",
        {"projectId": project_id, "page": 1, "limit": 20},
    )
    items = exports_res.get("items", []) if isinstance(exports_res, dict) else exports_res
    if isinstance(items, list):
        for item in items:
            if isinstance(item, dict) and item.get("id") == export_id:
                return item
    return None


def _poll_project_export(
    api_key: str,
    project_id: str,
    export_id: str,
    poll_interval: float = 1.8,
    max_wait: float = 240.0,
) -> dict[str, Any]:
    deadline = time.monotonic() + max_wait
    last_state = "pending"
    while time.monotonic() < deadline:
        status = rpc_call(api_key, "getExportStatus", {"projectExportId": export_id})
        state = str(status.get("state") or status.get("status") or "").lower()
        if state:
            last_state = state

        if state in ("failed", "error", "cancelled", "canceled"):
            raise RuntimeError(f"LucyLab export '{export_id}' failed: {status.get('error') or status}")

        item = _find_export_item(api_key, project_id, export_id)
        if item:
            item_status = str(item.get("status") or "").lower()
            audio_url = item.get("url") or item.get("mp3Url")
            if audio_url and (
                state in ("completed", "ready", "done", "succeeded")
                or item_status in ("completed", "ready", "done")
            ):
                return {
                    "audio_url": str(audio_url),
                    "srt_url": item.get("srtUrl") or status.get("srtUrl"),
                    "credits_used": status.get("creditsUsed"),
                }
            if item_status in ("failed", "error", "cancelled", "canceled"):
                raise RuntimeError(f"LucyLab export '{export_id}' failed with status '{item_status}'.")

        time.sleep(poll_interval)

    raise TimeoutError(
        f"Timed out waiting for LucyLab export '{export_id}' after {max_wait:.0f}s (last_state={last_state})."
    )


def _split_tiktok_chunks(text: str, max_bytes: int = 215) -> list[str]:
    """Split Vietnamese text on natural sentence/clause boundaries so each chunk fits TikTok's UTF-8 byte limit."""
    # Prevent hyphen between letters/digits from being read as 'đến'
    normalized = re.sub(r"(?<=[A-Za-zÀ-ỹ])-(?=[A-Za-zÀ-ỹ0-9])", " ", text)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    raw_sentences = [s.strip() for s in re.split(r"(?<=[.!?;])\s+", normalized) if s.strip()]

    chunks: list[str] = []
    for sent in raw_sentences:
        if len(sent.encode("utf-8")) <= max_bytes:
            chunks.append(sent)
            continue
        # Split long sentence by comma/clause boundaries
        clauses = [c.strip() for c in re.split(r"(?<=,)\s+", sent) if c.strip()]
        buf = ""
        for cl in clauses:
            cand = f"{buf} {cl}".strip() if buf else cl
            if len(cand.encode("utf-8")) <= max_bytes:
                buf = cand
            else:
                if buf:
                    chunks.append(buf)
                if len(cl.encode("utf-8")) <= max_bytes:
                    buf = cl
                else:
                    # Word-level split safety net
                    w_buf = ""
                    for word in cl.split():
                        w_cand = f"{w_buf} {word}".strip() if w_buf else word
                        if len(w_cand.encode("utf-8")) <= max_bytes:
                            w_buf = w_cand
                        else:
                            if w_buf:
                                chunks.append(w_buf)
                            w_buf = word
                    buf = w_buf
        if buf:
            chunks.append(buf)
    return chunks


def _invoke_tiktok_chunk(session_id: str, speaker: str, chunk_text: str) -> bytes:
    params = urllib.parse.urlencode(
        {
            "text_speaker": speaker,
            "req_text": chunk_text,
            "speaker_map_type": "0",
            "aid": "1233",
        }
    )
    last_err: Exception | None = None
    for ep in TIKTOK_ENDPOINTS:
        req = urllib.request.Request(
            f"{ep}?{params}",
            data=b"",
            headers={
                "User-Agent": TIKTOK_UA,
                "Cookie": f"sessionid={session_id}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=25) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
            status_code = payload.get("status_code")
            v_str = ((payload.get("data") or {}).get("v_str")) or ""
            if status_code == 0 and v_str:
                return base64.b64decode(v_str)
            last_err = RuntimeError(
                f"TikTok TTS returned status_code={status_code}, message={payload.get('message')}"
            )
        except Exception as exc:
            last_err = exc
    raise RuntimeError(f"TikTok TTS failed across all endpoints: {last_err}")


def synthesize_tiktok_cloud(
    text: str,
    output_path: Path,
    session_id: str,
    voice: str = "male",
    speed: float = 1.0,
    pause_duration: float = 0.22,
    sample_rate: int = 48000,
) -> dict[str, Any]:
    speaker = resolve_tiktok_speaker(voice)
    chunks = _split_tiktok_chunks(text)
    if not chunks:
        raise ValueError("Input text produced 0 valid TTS chunks.")

    ffmpeg_bin = shutil.which("ffmpeg")
    if not ffmpeg_bin:
        raise RuntimeError("FFmpeg is required to assemble TikTok TTS audio chunks.")

    with tempfile.TemporaryDirectory(prefix="tiktok_tts_") as tmp_dir:
        tmp_root = Path(tmp_dir)
        pcm_parts: list[bytes] = []
        silence_samples = max(0, int(round(pause_duration * sample_rate)))
        silence_pcm = b"\x00\x00" * silence_samples

        for idx, ch in enumerate(chunks):
            mp3_path = tmp_root / f"chunk_{idx:03d}.mp3"
            wav_path = tmp_root / f"chunk_{idx:03d}.wav"
            mp3_path.write_bytes(_invoke_tiktok_chunk(session_id, speaker, ch))
            subprocess.run(
                [
                    ffmpeg_bin,
                    "-y",
                    "-loglevel",
                    "error",
                    "-i",
                    str(mp3_path),
                    "-ar",
                    str(sample_rate),
                    "-ac",
                    "1",
                    "-c:a",
                    "pcm_s16le",
                    str(wav_path),
                ],
                check=True,
            )
            with wave.open(str(wav_path), "rb") as wf:
                raw_frames = wf.readframes(wf.getnframes())
            if idx > 0 and silence_pcm:
                pcm_parts.append(silence_pcm)
            pcm_parts.append(raw_frames)

        stitched_wav = tmp_root / "stitched.wav"
        with wave.open(str(stitched_wav), "wb") as wf_out:
            wf_out.setnchannels(1)
            wf_out.setsampwidth(2)
            wf_out.setframerate(sample_rate)
            wf_out.writeframes(b"".join(pcm_parts))

        final_out = convert_audio(stitched_wav, output_path, sample_rate=sample_rate, speed=speed)

    speaker_label = "Nam (BV075_streaming)" if speaker == "BV075_streaming" else f"Nữ ({speaker})"
    return {
        "provider": "tiktok",
        "output": str(final_out),
        "voice_id": speaker,
        "voice_name": f"TikTok Neural {speaker_label}",
        "speed": speed,
        "characters": len(text.strip()),
        "chunks": len(chunks),
        "credits_used": 0,
    }


def synthesize_lucylab_only(
    text: str,
    output_path: Path,
    api_key: str,
    env: dict[str, str],
    voice: str = "male",
    speed: float = 1.0,
    pause_duration: float = 0.25,
    model: str | None = None,
    sample_rate: int = 48000,
    keep_project: bool = False,
    save_srt: Path | None = None,
) -> dict[str, Any]:
    cleaned = text.strip()
    voice_id, voice_name = resolve_lucylab_voice(api_key, voice, env)
    project_name = f"ContinuumVO-{output_path.stem}"

    proj = rpc_call(
        api_key,
        "createProject",
        {"name": project_name, "userVoiceId": voice_id},
    )
    project_id = str(proj["id"])

    try:
        if model:
            rpc_call(
                api_key,
                "updateProjectModel",
                {"projectId": project_id, "model": model},
            )

        paragraphs = [p.strip() for p in cleaned.splitlines() if p.strip()]
        blocks = [
            {
                "text": para,
                "userVoiceId": voice_id,
                "speed": speed,
                "pauseDuration": pause_duration,
            }
            for para in paragraphs
        ]
        rpc_call(
            api_key,
            "updateProjectBlocks",
            {"projectId": project_id, "blocks": blocks},
        )

        export_res = rpc_call(
            api_key,
            "exportAudio",
            {"projectId": project_id},
        )
        export_id = str(export_res["projectExportId"])
        export_meta = _poll_project_export(api_key, project_id, export_id)

        with tempfile.TemporaryDirectory(prefix="lucylab_tts_") as tmp_dir:
            raw_dl = Path(tmp_dir) / "downloaded_audio"
            download_file(export_meta["audio_url"], raw_dl)
            final_out = convert_audio(raw_dl, output_path, sample_rate=sample_rate)

            if save_srt and export_meta.get("srt_url"):
                save_srt.resolve().parent.mkdir(parents=True, exist_ok=True)
                download_file(str(export_meta["srt_url"]), save_srt.resolve())
    finally:
        if not keep_project:
            try:
                rpc_call(api_key, "deleteProject", {"projectId": project_id})
            except Exception:
                pass

    return {
        "provider": "lucylab",
        "output": str(final_out),
        "voice_id": voice_id,
        "voice_name": voice_name,
        "project_id": project_id,
        "kept_project": keep_project,
        "speed": speed,
        "characters": len(cleaned),
        "credits_used": export_meta.get("credits_used"),
    }


def synthesize_cloud_vi(
    text: str,
    output_path: Path,
    voice: str = "male",
    provider: str = "auto",
    speed: float = 1.0,
    pause_duration: float = 0.22,
    model: str | None = None,
    sample_rate: int = 48000,
    keep_project: bool = False,
    save_srt: Path | None = None,
    env_file: Path = DEFAULT_ENV_FILE,
) -> dict[str, Any]:
    cleaned = text.strip()
    if not cleaned:
        raise ValueError("Input text cannot be empty.")

    env = load_env_file(env_file)
    api_key = env.get("VIETNAMESE_API_KEY", "").strip()
    tiktok_sid = env.get("TIKTOK_SESSION_ID", "").strip()
    prov = provider.strip().lower()

    if prov == "tiktok":
        if not tiktok_sid:
            raise RuntimeError(f"Missing TIKTOK_SESSION_ID in {env_file}")
        return synthesize_tiktok_cloud(
            text=cleaned,
            output_path=output_path,
            session_id=tiktok_sid,
            voice=voice,
            speed=speed,
            pause_duration=pause_duration,
            sample_rate=sample_rate,
        )

    if prov == "lucylab":
        if not api_key:
            raise RuntimeError(f"Missing VIETNAMESE_API_KEY in {env_file}")
        return synthesize_lucylab_only(
            text=cleaned,
            output_path=output_path,
            api_key=api_key,
            env=env,
            voice=voice,
            speed=speed,
            pause_duration=pause_duration,
            model=model,
            sample_rate=sample_rate,
            keep_project=keep_project,
            save_srt=save_srt,
        )

    # provider == "auto": Try LucyLab first; fall back to TikTok Cloud TTS if LucyLab has 0 credits
    if api_key:
        try:
            return synthesize_lucylab_only(
                text=cleaned,
                output_path=output_path,
                api_key=api_key,
                env=env,
                voice=voice,
                speed=speed,
                pause_duration=pause_duration,
                model=model,
                sample_rate=sample_rate,
                keep_project=keep_project,
                save_srt=save_srt,
            )
        except InsufficientCreditsError as cred_err:
            if not tiktok_sid:
                raise
            print(
                f"[Cloud TTS] Cảnh báo: {cred_err} -> Tự động chuyển sang TikTok Neural TTS "
                f"(sử dụng TIKTOK_SESSION_ID trong .env)."
            )
            return synthesize_tiktok_cloud(
                text=cleaned,
                output_path=output_path,
                session_id=tiktok_sid,
                voice=voice,
                speed=speed,
                pause_duration=pause_duration,
                sample_rate=sample_rate,
            )

    if tiktok_sid:
        return synthesize_tiktok_cloud(
            text=cleaned,
            output_path=output_path,
            session_id=tiktok_sid,
            voice=voice,
            speed=speed,
            pause_duration=pause_duration,
            sample_rate=sample_rate,
        )

    raise RuntimeError(f"Neither VIETNAMESE_API_KEY nor TIKTOK_SESSION_ID found in {env_file}")


def list_configured_voices(env_file: Path = DEFAULT_ENV_FILE) -> int:
    env = load_env_file(env_file)
    api_key = env.get("VIETNAMESE_API_KEY", "").strip()
    tiktok_sid = env.get("TIKTOK_SESSION_ID", "").strip()

    if api_key:
        ids: list[str] = []
        alias_map: dict[str, list[str]] = {}
        for alias, key in (("male (.env)", "VIETNAMESE_VOICEID_MALE"), ("female (.env)", "VIETNAMESE_VOICEID_FEMALE")):
            vid = env.get(key, "").strip()
            if vid:
                if vid not in ids:
                    ids.append(vid)
                alias_map.setdefault(vid, []).append(alias)

        for alias, vid in PRESET_VOICES.items():
            if vid not in ids:
                ids.append(vid)
            alias_map.setdefault(vid, []).append(f"preset:{alias}")

        voices = rpc_call(api_key, "getUserVoicesByIds", {"ids": ids})
        print("1. LucyLab JSON-RPC API (https://api.lucylab.io/json-rpc) — Đã cấu hình VIETNAMESE_API_KEY:")
        if isinstance(voices, list):
            for v in voices:
                vid = v.get("id", "")
                aliases = ", ".join(alias_map.get(vid, [])) or "custom"
                name = v.get("name", "(unknown)")
                active = "ACTIVE" if v.get("isActive") else "INACTIVE (tự động fallback TVC 4 khi dùng male)"
                model_name = (v.get("modelInfo") or {}).get("model", "unknown")
                desc = (v.get("description") or "").strip()
                print(f"   - [{aliases}] {name} (id={vid}, model={model_name}, status={active})")
                if desc:
                    print(f"       Mô tả: {desc}")
    else:
        print("1. LucyLab JSON-RPC API: Chưa cấu hình VIETNAMESE_API_KEY.")

    if tiktok_sid:
        print("\n2. TikTok Neural Vietnamese TTS (Fallback / Direct qua TIKTOK_SESSION_ID) — SẴN SÀNG:")
        print("   - [male]   BV075_streaming (Giọng Nam Tiếng Việt Neural 24kHz)")
        print("   - [female] BV074_streaming (Giọng Nữ Tiếng Việt Neural 24kHz)")
    else:
        print("\n2. TikTok Neural Vietnamese TTS: Chưa cấu hình TIKTOK_SESSION_ID.")

    return 0


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="Tạo giọng thuyết minh Tiếng Việt Cloud AI qua LucyLab JSON-RPC & TikTok Neural TTS."
    )
    parser.add_argument("-t", "--text", type=str, default="", help="Nội dung văn bản cần đọc.")
    parser.add_argument("-i", "--input-file", type=Path, default=None, help="File kịch bản .txt (UTF-8).")
    parser.add_argument("-o", "--output", type=Path, default=Path("voiceover.wav"), help="File .wav/.mp3 đầu ra.")
    parser.add_argument(
        "-v",
        "--voice",
        type=str,
        default="male",
        help="Chọn 'male', 'female', 'tvc4', 'trung-quan', 'quang-anh', hoặc voiceId.",
    )
    parser.add_argument(
        "-p",
        "--provider",
        choices=("auto", "lucylab", "tiktok"),
        default="auto",
        help="Nhà cung cấp TTS: 'auto' (ưu tiên LucyLab, hết credit tự chuyển TikTok), 'lucylab', hoặc 'tiktok'.",
    )
    parser.add_argument("--speed", type=float, default=1.0, help="Tốc độ đọc (mặc định: 1.0).")
    parser.add_argument("--pause", type=float, default=0.22, help="Khoảng nghỉ giữa các câu tính bằng giây (mặc định: 0.22).")
    parser.add_argument("--model", type=str, default=None, help="Tên model LucyLab tùy chọn (ví dụ: lucyV2).")
    parser.add_argument("--sample-rate", type=int, default=48000, help="Sample rate khi xuất WAV (mặc định: 48000).")
    parser.add_argument("--save-srt", type=Path, default=None, help="Lưu thêm file .srt gốc từ LucyLab nếu có.")
    parser.add_argument("--keep-project", action="store_true", help="Giữ lại project trên dashboard LucyLab sau khi xuất.")
    parser.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE, help="Đường dẫn file .env.")
    parser.add_argument("--list-voices", action="store_true", help="Kiểm tra kết nối & hiển thị giọng đọc từ .env.")

    args = parser.parse_args()

    if args.list_voices:
        return list_configured_voices(args.env_file)

    content = args.text
    if args.input_file:
        content = args.input_file.read_text(encoding="utf-8")
    if not content.strip():
        parser.error("Vui lòng truyền --text hoặc --input-file có nội dung văn bản.")

    meta = synthesize_cloud_vi(
        text=content,
        output_path=args.output,
        voice=args.voice,
        provider=args.provider,
        speed=args.speed,
        pause_duration=args.pause,
        model=args.model,
        sample_rate=args.sample_rate,
        keep_project=args.keep_project,
        save_srt=args.save_srt,
        env_file=args.env_file,
    )
    print(
        f"[{meta['provider'].upper()} TTS] Đã xuất giọng đọc thành công "
        f"(voice='{meta['voice_name']}', {meta['characters']} ký tự): {meta['output']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

