#!/bin/bash
# MOSS-TTS-Nano 语音克隆 + 分句拼接 + 1.1x 加速脚本
# 用法: ./moss_clone.sh "要朗读的文本" [--output output.wav]
#    或: ./moss_clone.sh --file script.txt [--output output.wav]
#    不带参数: 使用默认文本

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REF_AUDIO="${SCRIPT_DIR}/tts/laoxin0510.wav"
OUTPUT_DIR="${SCRIPT_DIR}/audio"
CONCAT_TXT="/tmp/moss_concat_list.txt"
SPEED="1.1"

TEXT=""
INPUT_FILE=""
OUTPUT_FILE="${OUTPUT_DIR}/narration.wav"

while [[ $# -gt 0 ]]; do
  case $1 in
    --file)
      INPUT_FILE="$2"
      shift 2
      ;;
    --output)
      OUTPUT_FILE="$2"
      shift 2
      ;;
    -h|--help)
      echo "用法: $0 [--file script.txt] \"文本\" [--output output.wav]"
      echo "  --file FILE      从文件读取文本"
      echo "  --output FILE    输出文件路径 (默认: audio/narration.wav)"
      exit 0
      ;;
    *)
      TEXT="$1"
      shift
      ;;
  esac
done

if [[ -z "$TEXT" && -z "$INPUT_FILE" ]]; then
  TEXT="特斯拉美国地区在售的Model S、X车型已涨价。据特斯拉官方平台4月23日数据显示，Model 3、Model Y等主销车型的售价保持不变。这一涨价策略令不少消费者感到意外。财经评论员分析指出，特斯拉此次涨价可能与成本上涨及市场需求变化有关。与此同时，国内新能源汽车市场竞争日趋激烈。分析师普遍认为，这对消费者而言或意味着购车成本将进一步上升。"
fi

if [[ -n "$INPUT_FILE" ]]; then
  TEXT=$(cat "$INPUT_FILE")
fi

if [[ ! -f "$REF_AUDIO" ]]; then
  echo "错误: 参考音频不存在: $REF_AUDIO"
  exit 1
fi

if ! command -v ffmpeg &>/dev/null; then
  echo "错误: ffmpeg 未安装"
  exit 1
fi

# 使用 Python 脚本调用 MOSS，避免 shell 中文编码问题
PYTHON_SCRIPT="/tmp/moss_call_$$.py"
cat > "$PYTHON_SCRIPT" << 'PYEOF'
import sys
import os

text = sys.argv[1]
output = sys.argv[2]
ref_audio = sys.argv[3]

idx = os.urandom(4).hex()
out = f"/tmp/part_{idx}.wav"

import subprocess
cmd = [
    "/opt/homebrew/Caskroom/miniforge/base/envs/moss-tts-nano/bin/python",
    "/tmp/MOSS-TTS-Nano/infer.py",
    "--checkpoint", "/tmp/MOSS-TTS-Nano/models/MOSS-TTS-Nano",
    "--audio-tokenizer-pretrained-name-or-path", "/tmp/MOSS-TTS-Nano/models/MOSS-Audio-Tokenizer-Nano",
    "--prompt-audio-path", ref_audio,
    "--text", text,
    "--dtype", "float32",
    "--mode", "voice_clone",
    "--audio-temperature", "0.5",
    "--text-temperature", "0.3",
    "--output-audio-path", out,
    "--disable-wetext-processing",
    "--max-new-frames", "300",
    "--audio-repetition-penalty", "1.5",
    "--audio-top-k", "15"
]
subprocess.run(cmd, check=True)
print(out)
PYEOF

RAW_FILE="/tmp/moss_raw.wav"
rm -f /tmp/part_*.wav "${RAW_FILE}" "${OUTPUT_FILE}" "${CONCAT_TXT}" /tmp/moss_text_*.txt

# 将文本写入文件供 Python 读取
TEXT_FILE="/tmp/moss_text_$$.txt"
printf '%s' "$TEXT" > "${TEXT_FILE}"

# 读取文本并按句号分割
python3 << PYREAD
text = open("${TEXT_FILE}", "r", encoding="utf-8").read()
# 按句号分割
import re
sentences = re.split(r'([。！？])', text)
# 合并句号到前一句
merged = []
for i in range(0, len(sentences)-1, 2):
    if i+1 < len(sentences):
        merged.append(sentences[i] + sentences[i+1])
    else:
        merged.append(sentences[i])
with open("${TEXT_FILE}", "w", encoding="utf-8") as f:
    for s in merged:
        if s.strip():
            f.write(s.strip() + "\n")
PYREAD

while IFS= read -r sentence || [[ -n "$sentence" ]]; do
  sentence=$(echo "$sentence" | xargs)
  [[ -z "$sentence" ]] && continue

  echo "生成: $sentence"

  out=$(python3 "$PYTHON_SCRIPT" "$sentence" "$OUTPUT_FILE" "$REF_AUDIO")
  echo "  -> $(ffprobe -v error -show_entries format=duration -of csv=p=0 "$out")s"
done < "${TEXT_FILE}"

ls /tmp/part_*.wav 2>/dev/null | sort | while read f; do echo "file '$f'"; done > "${CONCAT_TXT}"

if [[ $(wc -l < "${CONCAT_TXT}") -eq 0 ]]; then
  echo "错误: 没有生成任何音频文件"
  rm -f "$PYTHON_SCRIPT" "${TEXT_FILE}"
  exit 1
fi

echo ""
echo "拼接 $(wc -l < "${CONCAT_TXT}") 个片段..."
ffmpeg -y -f concat -safe 0 -i "${CONCAT_TXT}" -c:a pcm_s16le "${RAW_FILE}" 2>/dev/null

echo "加速 ${SPEED}x..."
ffmpeg -y -i "${RAW_FILE}" -filter:a "atempo=${SPEED}" -q:a 0 "${OUTPUT_FILE}" 2>/dev/null

dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "${OUTPUT_FILE}")
echo "完成: ${OUTPUT_FILE} (${dur}s)"

rm -f /tmp/part_*.wav "${RAW_FILE}" "${CONCAT_TXT}" /tmp/moss_text_*.txt "$PYTHON_SCRIPT"