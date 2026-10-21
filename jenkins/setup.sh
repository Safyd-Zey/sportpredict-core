#!/usr/bin/env bash
# One-command local CI/CD lab: kind cluster for CD + Jenkins controller configured as code.
# Requires Docker (with buildx), kind and kubectl on the host.
set -euo pipefail
cd "$(dirname "$0")"

CLUSTER="${KIND_CLUSTER:-sportpredict}"

if ! kind get clusters | grep -qx "$CLUSTER"; then
  kind create cluster --name "$CLUSTER" --config kind-cluster.yaml --wait 120s
fi

# Jenkins joins the "kind" network, so it uses the cluster's internal API address.
mkdir -p secrets
kind get kubeconfig --internal --name "$CLUSTER" > secrets/kubeconfig
chmod 644 secrets/kubeconfig

if [[ ! -f .env ]]; then
  {
    echo "DOCKER_GID=$(getent group docker | cut -d: -f3)"
    echo "JENKINS_ADMIN_PASSWORD=$(head -c 18 /dev/urandom | base64 | tr -d '/+=')"
    echo "KIND_CLUSTER=$CLUSTER"
    echo "DOCKERHUB_REPO="
  } > .env
  echo "Created jenkins/.env (admin password inside)."
fi

docker compose up -d --build
echo "Jenkins: http://localhost:8080  (user: admin, password: see jenkins/.env)"
echo "API after the first deployment: http://localhost:30080/health"
