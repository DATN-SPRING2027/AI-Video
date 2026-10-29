#!/usr/bin/env python3
"""
Piper TTS Offline Voiceover CLI for CreateVideo Studio.
Uses relative ASCII paths from BASE_DIR so C/C++ extensions (espeak-ng & ONNX Runtime)
work reliably even inside Windows directories containing Unicode diacritics (e.g. KÌ / ĐATN).
"""
from __future__ import annotations

import argparse
import os
import sys
import wave
from pathlib import Path

import numpy as np
from piper.config import SynthesisConfig
from piper.voice import PiperVoice

BASE_DIR = Path(__file__).resolve().parent
VOICES_DIR = BASE_DIR / "voices"
DEFAULT_VOICE = "vi_VN-vais1000-medium"


def list_installed_voices() -> list[str]:
    if not VOICES_DIR.exists():
        return []
    return sorted(p.stem for p in VOICES_DIR.glob("*.onnx"))


def synthesize(
    text: str,
    output_wav: Path,
    voice: str = DEFAULT_VOICE,
    length_scale: float = 1.0,
    sentence_silence: float = 0.25,
) -> Path:
    output_abs = output_wav.resolve()
    output_abs.parent.mkdir(parents=True, exist_ok=True)

    candidate = Path(voice)
    if not candidate.exists():
        candidate = VOICES_DIR / f"{voice}.onnx"
    if not candidate.exists():
        available = ", ".join(list_installed_voices()) or "(none)"
        raise FileNotFoundError(
            f"Không tìm thấy giọng đọc '{voice}' tại {candidate}. Các giọng hiện có: {available}"
        )
    model_abs = candidate.resolve()

    prev_cwd = Path.cwd()
    try:
        os.chdir(BASE_DIR)
        espeak_rel = os.path.relpath(
            BASE_DIR / ".venv" / "Lib" / "site-packages" / "piper" / "espeak-ng-data",
            BASE_DIR,
        )
        try:
            model_rel = os.path.relpath(model_abs, BASE_DIR)
        except ValueError:
            model_rel = str(model_abs)

        piper_voice = PiperVoice.load(
            model_path=model_rel,
            config_path=f"{model_rel}.json",
            espeak_data_dir=espeak_rel,
        )
        syn_cfg = SynthesisConfig(length_scale=length_scale)

        with wave.open(str(output_abs), "wb") as wav_out:
            first_chunk = True
            silence_bytes = b""
            for chunk in piper_voice.synthesize(text.strip(), syn_config=syn_cfg):
                if first_chunk:
                    wav_out.setframerate(chunk.sample_rate)
                    wav_out.setsampwidth(chunk.sample_width)
                    wav_out.setnchannels(chunk.sample_channels)
                    if sentence_silence > 0:
                        n_silence = int(round(chunk.sample_rate * sentence_silence))
                        silence_bytes = np.zeros(n_silence, dtype=np.int16).tobytes()
                    first_chunk = False
                elif silence_bytes:
                    wav_out.writeframes(silence_bytes)
                wav_out.writeframes(chunk.audio_int16_bytes)
    finally:
        os.chdir(prev_cwd)

    return output_abs


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="Tạo giọng thuyết minh (.wav) offline bằng Piper TTS (Tiếng Việt & Tiếng Anh)."
    )
    parser.add_argument("-t", "--text", type=str, default="", help="Nội dung văn bản cần đọc.")
    parser.add_argument("-i", "--input-file", type=Path, default=None, help="File kịch bản .txt (UTF-8).")
    parser.add_argument("-o", "--output", type=Path, default=Path("voiceover.wav"), help="File .wav đầu ra.")
    parser.add_argument(
        "-v",
        "--voice",
        type=str,
        default=DEFAULT_VOICE,
        help=f"Tên giọng đọc trong voices/ (mặc định: {DEFAULT_VOICE}).",
    )
    parser.add_argument(
        "--length-scale",
        type=float,
        default=1.0,
        help="Tốc độ đọc (<1.0 đọc nhanh hơn, >1.0 đọc chậm hơn, mặc định: 1.0).",
    )
    parser.add_argument(
        "--sentence-silence",
        type=float,
        default=0.25,
        help="Khoảng nghỉ giữa các câu tính bằng giây (mặc định: 0.25).",
    )
    parser.add_argument("--list-voices", action="store_true", help="Liệt kê các giọng đọc đã cài đặt.")

    args = parser.parse_args()

    if args.list_voices:
        print("Các giọng đọc Piper TTS đã cài đặt:")
        for v in list_installed_voices():
            print(f"  - {v}")
        return 0

    content = args.text
    if args.input_file:
        content = args.input_file.read_text(encoding="utf-8")
    if not content.strip():
        parser.error("Vui lòng truyền --text hoặc --input-file có nội dung văn bản.")

    out_path = synthesize(
        text=content,
        output_wav=args.output,
        voice=args.voice,
        length_scale=args.length_scale,
        sentence_silence=args.sentence_silence,
    )
    print(f"[Piper TTS] Đã xuất giọng đọc thành công: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
