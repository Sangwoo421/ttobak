"""Windows 내장 한국어 음성(Microsoft Heami)으로 합성하는 오프라인 TTS.

왜 있나: Gemini TTS 미리보기 모델은 무료 등급에서 **하루 10회** 로 막힌다(429, 2026-09-09 실측).
그때 무음을 내보내면 어르신 화면이 "고장"으로 보인다. 목소리가 조금 기계적이어도 소리가 나는 쪽이
낫다. 시연 노트북이 Windows 이므로 API 없이 항상 동작한다.

is_fallback=True 로 돌려준다 — audio_cache 가 이 결과를 캐시하지 않으므로, 다음 호출에서는
다시 Gemini 를 시도하고 성공하면 그때 캐시된다. 무음 대체본과 같은 규칙이다.
"""
from __future__ import annotations

import logging
import os
import subprocess
import sys
import tempfile

logger = logging.getLogger(__name__)

_VOICE = "Microsoft Heami Desktop"
# 어르신 모드: 조금 느리게. 확인 톤은 더 또박또박.
_RATE = {"friendly": -2, "confirm": -3}

_PS = r"""
Add-Type -AssemblyName System.Speech
$syn = New-Object System.Speech.Synthesis.SpeechSynthesizer
try { $syn.SelectVoice('%(voice)s') } catch { }
$syn.Rate = %(rate)d
$fmt = New-Object System.Speech.AudioFormat.SpeechAudioFormatInfo(24000, [System.Speech.AudioFormat.AudioBitsPerSample]::Sixteen, [System.Speech.AudioFormat.AudioChannel]::Mono)
$syn.SetOutputToWaveFile('%(out)s', $fmt)
$text = [System.IO.File]::ReadAllText('%(txt)s', [System.Text.Encoding]::UTF8)
$syn.Speak($text)
$syn.SetOutputToNull()
$syn.Dispose()
"""


def available() -> bool:
    return sys.platform == "win32"


class SapiTTSProvider:
    def __init__(self, voice: str = _VOICE) -> None:
        self._voice = voice

    def synthesize(self, text: str, tone: str = "friendly") -> tuple[bytes, str, bool]:
        with tempfile.TemporaryDirectory() as d:
            txt = os.path.join(d, "t.txt")
            out = os.path.join(d, "o.wav")
            with open(txt, "w", encoding="utf-8") as f:
                f.write(text)
            script = _PS % {
                "voice": self._voice.replace("'", "''"),
                "rate": _RATE.get(tone, _RATE["friendly"]),
                "out": out.replace("'", "''"),
                "txt": txt.replace("'", "''"),
            }
            subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", script],
                check=True, capture_output=True, timeout=30,
            )
            with open(out, "rb") as f:
                audio = f.read()
        if len(audio) < 1000:
            raise RuntimeError("SAPI produced no audio")
        return audio, "wav", True
