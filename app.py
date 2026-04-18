import os
import json
import uuid
from flask import Flask, request, jsonify
from google.cloud import pubsub_v1

app = Flask(__name__)

PROJECT_ID = os.environ.get("PROJECT_ID")
TOPIC_ID = os.environ.get("TOPIC_ID", "estimate-pi-topic")

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)

@app.route("/estimate_pi", methods=["POST"])
def estimate_pi_request():
    data = request.get_json(silent=True)

    if not data or "total_points" not in data:
        return jsonify({"error": "Missing total_points"}), 400

    total_points = data["total_points"]

    if not isinstance(total_points, int) or total_points <= 0:
        return jsonify({"error": "total_points must be a positive integer"}), 400

    job_id = str(uuid.uuid4())

    event = {
        "job_id": job_id,
        "total_points": total_points
    }

    publisher.publish(topic_path, json.dumps(event).encode("utf-8"))

    return jsonify({
        "message": "Job accepted",
        "job_id": job_id,
        "status": "queued"
    }), 202

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)