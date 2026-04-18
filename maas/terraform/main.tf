terraform {
  required_version = ">= 1.5.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

variable "project_id" {
  type = string
}

variable "region" {
  type    = string
  default = "us-central1"
}

variable "receiver_image" {
  type = string
}

variable "worker_image" {
  type = string
}

data "google_project" "current" {
  project_id = var.project_id
}

resource "google_pubsub_topic" "pi_jobs" {
  name = "pi-jobs"
}

resource "google_service_account" "receiver_service" {
  account_id   = "receiver-service-sa"
  display_name = "Receiver Service Account"
}

resource "google_service_account" "worker_service" {
  account_id   = "worker-service-sa"
  display_name = "Worker Service Account"
}

resource "google_project_iam_member" "receiver_publisher" {
  project = var.project_id
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${google_service_account.receiver_service.email}"
}

resource "google_project_iam_member" "worker_firestore" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.worker_service.email}"
}

resource "google_cloud_run_v2_service" "receiver" {
  name     = "receiver-service"
  location = var.region

  template {
    service_account = google_service_account.receiver_service.email

    containers {
      image = var.receiver_image

      env {
        name  = "PROJECT_ID"
        value = var.project_id
      }

      env {
        name  = "TOPIC_ID"
        value = google_pubsub_topic.pi_jobs.name
      }
    }
  }

  depends_on = [google_project_iam_member.receiver_publisher]
}

resource "google_cloud_run_v2_service" "worker" {
  name     = "worker-service"
  location = var.region

  template {
    service_account = google_service_account.worker_service.email

    containers {
      image = var.worker_image
    }
  }

  depends_on = [google_project_iam_member.worker_firestore]
}

resource "google_cloud_run_v2_service_iam_member" "receiver_public" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.receiver.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# This service account is only for Pub/Sub push auth.
resource "google_service_account" "pubsub_push" {
  account_id   = "pubsub-push-sa"
  display_name = "PubSub Push Service Account"
}

resource "google_service_account_iam_member" "pubsub_token_creator" {
  service_account_id = google_service_account.pubsub_push.name
  role               = "roles/iam.serviceAccountTokenCreator"
  member             = "serviceAccount:service-${data.google_project.current.number}@gcp-sa-pubsub.iam.gserviceaccount.com"
}

resource "google_cloud_run_v2_service_iam_member" "worker_invoker" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.worker.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.pubsub_push.email}"
}

resource "google_pubsub_subscription" "worker_subscription" {
  name  = "pi-jobs-subscription"
  topic = google_pubsub_topic.pi_jobs.name

  push_config {
    push_endpoint = google_cloud_run_v2_service.worker.uri

    oidc_token {
      service_account_email = google_service_account.pubsub_push.email
    }
  }

  depends_on = [
    google_cloud_run_v2_service.worker,
    google_cloud_run_v2_service_iam_member.worker_invoker,
    google_service_account_iam_member.pubsub_token_creator,
  ]
}

output "api_url" {
  value = google_cloud_run_v2_service.receiver.uri
}
