import json
import os
import uuid

from flask import Flask, jsonify, request
from google.cloud import pubsub_v1


app = Flask(__name__)

project_id = os.getenv("PROJECT_ID", "")
topic_id = os.getenv("TOPIC_ID", "pi-jobs")
publisher = pubsub_v1.PublisherClient()


@app.route("/estimate_pi", methods=["POST"])
def estimate_pi():
    data = request.get_json(silent=True)

    if not data or "total_points" not in data:
        return jsonify({"error": "total_points is required"}), 400

    total_points = data["total_points"]

    if not isinstance(total_points, int) or total_points <= 0:
        return jsonify({"error": "total_points must be a positive integer"}), 400

    if not project_id:
        return jsonify({"error": "PROJECT_ID is not set"}), 500

    job_id = str(uuid.uuid4())
    topic_path = publisher.topic_path(project_id, topic_id)

    message = {
        "job_id": job_id,
        "total_points": total_points,
    }

    publisher.publish(topic_path, json.dumps(message).encode("utf-8"))

    return (
        jsonify(
            {
                "message": "Job accepted",
                "job_id": job_id,
                "status": "queued",
            }
        ),
        202,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
