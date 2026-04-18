import os
import json
import random
from datetime import datetime, timezone
from flask import Flask, request, jsonify
from google.cloud import firestore

app = Flask(__name__)
db = firestore.Client()

def estimate_pi(n):
    inside_circle = 0
    for _ in range(n):
        x, y = random.uniform(-1, 1), random.uniform(-1, 1)
        if x**2 + y**2 <= 1:
            inside_circle += 1
    return (4 * inside_circle) / n

@app.route("/", methods=["POST"])
def process_event():
    envelope = request.get_json(silent=True)

    if not envelope:
        return jsonify({"error": "No event received"}), 400

    # Pub/Sub push usually wraps data in message.data (base64),
    # but for a simplified course solution you can also send JSON directly.
    if "message" in envelope and "data" in envelope["message"]:
        import base64
        payload = json.loads(base64.b64decode(envelope["message"]["data"]).decode("utf-8"))
    else:
        payload = envelope

    job_id = payload["job_id"]
    total_points = payload["total_points"]

    pi_value = estimate_pi(total_points)

    doc = {
        "job_id": job_id,
        "total_points": total_points,
        "pi_estimate": pi_value,
        "status": "completed",
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    db.collection("pi_jobs").document(job_id).set(doc)

    print(json.dumps({
        "severity": "INFO",
        "message": "Pi estimation completed",
        "job_id": job_id,
        "total_points": total_points,
        "pi_estimate": pi_value
    }))

    return jsonify({"status": "done"}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)