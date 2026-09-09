#!/bin/bash
# ai-server/audio_cache/ 를 비운다.
#
# 언제 쓰나: 캐시된 음성을 전부 버리고 다음 호출부터 새로 굽고 싶을 때.
# (폴백/무음은 이제 캐시에 안 들어가지만, 예전 빌드가 남긴 파일이나
#  모델·목소리를 바꾼 뒤 옛 합성본을 지우고 싶을 때 쓴다.)
#
# 사용: ./tools/clear-audio-cache.sh
set -euo pipefail
DIR="$(cd "$(dirname "$0")/.." && pwd)/ai-server/audio_cache"

if [ ! -d "$DIR" ]; then
  echo "audio_cache 디렉터리 없음: $DIR (아무것도 안 함)"
  exit 0
fi

count=$(find "$DIR" -type f -name '*.wav' | wc -l | tr -d ' ')
find "$DIR" -type f -name '*.wav' -delete
echo "── audio_cache 비움 ── ($count개 삭제) $DIR"
