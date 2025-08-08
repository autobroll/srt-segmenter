from flask import Flask, request, jsonify
import re
from datetime import timedelta

app = Flask(__name__)

# --- Fonctions utilitaires ---
def srt_time_to_seconds(time_str):
    hours, minutes, seconds_millis = time_str.split(':')
    seconds, millis = seconds_millis.split(',')
    return int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(millis) / 1000


# --- Endpoint santé ---
@app.get("/health")
def health():
    return {"ok": True}, 200


# --- Endpoint /prepare ---
@app.post("/prepare")
def prepare():
    srt_text = ""

    # Accepte JSON
    if request.is_json:
        data = request.get_json(silent=True) or {}
        srt_text = data.get("srt", "").strip()

    # Accepte multipart/form-data
    elif request.form:
        srt_text = request.form.get("srt", "").strip()

    if not srt_text:
        return jsonify({"error": "No SRT provided"}), 400

    # Ici tu peux faire un pré-traitement si nécessaire
    return jsonify({"srt": srt_text})


# --- Endpoint /segment ---
@app.post("/segment")
def segment_srt():
    try:
        srt_text = ""

        # 📌 Si JSON
        if request.is_json:
            data = request.get_json(silent=True) or {}
            print("🟢 Requête JSON reçue :", data)
            srt_text = data.get("srt", "")

        # 📌 Si multipart/form-data
        elif request.form:
            print("🟢 Requête FORM reçue :", dict(request.form))
            srt_text = request.form.get("srt", "")

        print("📥 Contenu SRT reçu :", srt_text)

        if not srt_text.strip():
            print("🔴 Erreur : aucun texte SRT fourni")
            return jsonify({"error": "No SRT text provided"}), 400

        # --- Découpage en blocs de 10 secondes ---
        pattern = r"(\d+)\s+(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\s+([\s\S]*?)(?=\n\n|\Z)"
        matches = re.findall(pattern, srt_text)
        print(f"🔍 {len(matches)} blocs détectés dans le SRT")

        blocks = {}
        for index, start_time, end_time, text in matches:
            start_sec = srt_time_to_seconds(start_time)
            group_id = int(start_sec // 10)
            blocks.setdefault(group_id, []).append(text.strip().replace("\n", " "))

        # --- Format final ---
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

        print("✅ Résultat final :", output)
        return jsonify({"data": output})

    except Exception as e:
        print("🔥 Erreur serveur :", str(e))
        return jsonify({"error": str(e)}), 500


# --- Point d'entrée ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
