#!/usr/bin/bash

set -ex

CLUSTER_APP_TAG=ynr

CLUSTER_LIST=$(aws ecs list-clusters | jq -r '.clusterArns|map(split("/")[1])[]')

# Force an error if we have a count of matching clusters that differs from 1
CLUSTER_NAME=$(aws ecs describe-clusters --include TAGS --cluster "${CLUSTER_LIST}" | jq -r --arg TAG "${CLUSTER_APP_TAG}" '.clusters|map(.tags = (.tags|from_entries)) | map(select(.tags.app == $TAG and  .status == "ACTIVE" ))|map(.clusterName)| if .|length != 1 then halt_error else .[0] end ')
mapfile -t SERVICE_LIST < <(aws ecs list-services  --cluster "${CLUSTER_NAME}" | jq -r '.serviceArns|map(split("/")[2])[]')

services_info=$(aws ecs describe-services  --cluster "${CLUSTER_NAME}" --services "${SERVICE_LIST[@]}" --include TAGS | jq '.services|map({name: .serviceName, tags: (.tags // [] |from_entries) })')
web_service_name=$(echo "$services_info" | jq -r --arg ROLE_TAG "web" 'map(select(.tags.role == $ROLE_TAG ))|map(.name) | if .|length != 1 then halt_error else .[0] end')
queue_service_name=$(echo "$services_info" | jq -r --arg ROLE_TAG "queue" 'map(select(.tags.role == $ROLE_TAG ))|map(.name) | if .|length != 1 then halt_error else .[0] end')

echo "web service name: ${web_service_name}"
echo "queue service name: ${queue_service_name}"

echo Waiting for the two services.
# Waiting is (intentionally) a blocking action. We can't wait for both at the
# same time in one command, but our workaround is to wait for one and then the
# other. If they finish in the other order then the second 'wait' will be
# neglible.

aws ecs wait services-stable --cluster "$CLUSTER_NAME" --service "${web_service_name}"
aws ecs wait services-stable --cluster "$CLUSTER_NAME" --service "${queue_service_name}"
