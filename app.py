from flask import Flask, request, jsonify
import re
from datetime import timedelta

app = Flask(__name__)

def srt_time_to_seconds(time_str):
    hours, minutes, seconds_millis = time_str.split(':')
    seconds, millis = seconds_millis.split(',')
    return int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(millis) / 1000

@app.route('/segment', methods=['POST'])
def segment_srt():
    srt_text = request.json.get("srt")
    if not srt_text:
        return jsonify({"error": "No SRT text provided"}), 400

    pattern = r"(\d+)\s+(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\s+([\s\S]*?)(?=\n\n|\Z)"
    matches = re.findall(pattern, srt_text)

    blocks = {}

    for index, start_time, end_time, text in matches:
        start_sec = srt_time_to_seconds(start_time)
        group_id = int(start_sec // 10)

        if group_id not in blocks:
            blocks[group_id] = []

        blocks[group_id].append(text.strip().replace("\n", " "))

    # Format final : tableau de blocs
    output = []
    for gid in sorted(blocks):
        start = str(timedelta(seconds=gid * 10))
        end = str(timedelta(seconds=(gid + 1) * 10))
        full_text = " ".join(blocks[gid])
        output.append({
            "start": start,
            "end": end,
            "text": full_text
        })

    return jsonify(output)

if __name__ == '__main__':
    app.run(port=5000, debug=True)
