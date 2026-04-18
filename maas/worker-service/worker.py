import base64
import json
import random
from datetime import datetime, timezone

from flask import Flask, jsonify, request
from google.cloud import firestore


app = Flask(__name__)
db = firestore.Client(database="swe-455")


def estimate_pi(n):
    inside_circle = 0
    for _ in range(n):
        x, y = random.uniform(-1, 1), random.uniform(-1, 1)
        if x**2 + y**2 <= 1:
            inside_circle += 1
    return (4 * inside_circle) / n


@app.route("/", methods=["POST"])
def handle_event():
    body = request.get_json(silent=True) or {}
    message = body.get("message", {})
    encoded_data = message.get("data")

    if not encoded_data:
        return jsonify({"error": "Pub/Sub message data is missing"}), 400

    try:
        decoded_data = base64.b64decode(encoded_data).decode("utf-8")
        event_data = json.loads(decoded_data)
    except Exception:
        return jsonify({"error": "Could not decode Pub/Sub message"}), 400

    job_id = event_data.get("job_id")
    total_points = event_data.get("total_points")

    if not job_id or not isinstance(total_points, int) or total_points <= 0:
        return jsonify({"error": "Invalid job data"}), 400

    pi_value = estimate_pi(total_points)

    db.collection("pi_jobs").document(job_id).set(
        {
            "job_id": job_id,
            "total_points": total_points,
            "pi_estimate": pi_value,
            "status": "done",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    )

    return jsonify({"message": "Job processed"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
