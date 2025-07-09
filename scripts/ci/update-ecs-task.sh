#!/usr/bin/bash

set -ex

CLUSTER_APP_TAG=ynr
SERVICE_ROLE_TAG=web

CLUSTER_LIST=$(aws ecs list-clusters | jq -r '.clusterArns|map(split("/")[1])[]')

# Force an error if we have a count of matching clusters that differs from 1
CLUSTER_NAME=$(aws ecs describe-clusters --include TAGS --cluster "${CLUSTER_LIST}" | jq -r --arg TAG "${CLUSTER_APP_TAG}" '.clusters|map(.tags = (.tags|from_entries)) | map(select(.tags.app == $TAG and  .status == "ACTIVE" ))|map(.clusterName)| if .|length != 1 then halt_error else .[0] end ')
SERVICE_LIST=$(aws ecs list-services  --cluster "${CLUSTER_NAME}" | jq -r '.serviceArns|map(split("/")[2])[]')

# Force an error if we have a count of matching services that differs from 1
SERVICE_NAME=$(aws ecs describe-services  --cluster "${CLUSTER_NAME}" --service "${SERVICE_LIST}" --include TAGS | jq -r --arg TAG "${SERVICE_ROLE_TAG}" '.services|map(.tags = (.tags|from_entries)) | map(select(.tags.role == $TAG ))|map(.serviceName)| if .|length != 1 then halt_error else .[0] end ')

aws ecs update-service --cluster "$CLUSTER_NAME" --service "$SERVICE_NAME" --force-new-deployment

echo "done"
