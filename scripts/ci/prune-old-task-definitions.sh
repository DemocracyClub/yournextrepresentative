#!/usr/bin/bash

set -ex


CLUSTER_APP_TAG=ynr
SERVICE_ROLE_TAG=web
KEEP_COUNT=5


echo "Tidying old task definitions for service ${SERVICE_ROLE_TAG} in cluster ${CLUSTER_APP_TAG}"

CLUSTER_LIST=$(aws ecs list-clusters | jq -r '.clusterArns|map(split("/")[1])[]')

# Force an error if we have a count of matching clusters that differs from 1
CLUSTER_NAME=$(aws ecs describe-clusters --include TAGS --cluster "${CLUSTER_LIST}" | jq -r --arg TAG "${CLUSTER_APP_TAG}" '.clusters|map(.tags = (.tags|from_entries)) | map(select(.tags.app == $TAG and  .status == "ACTIVE" ))|map(.clusterName)| if .|length != 1 then halt_error else .[0] end ')
SERVICE_LIST=$(aws ecs list-services  --cluster "${CLUSTER_NAME}" | jq -r '.serviceArns|map(split("/")[2])[]')

# Force an error if we have a count of matching services that differs from 1
SERVICE_NAME=$(aws ecs describe-services  --cluster "${CLUSTER_NAME}" --service "${SERVICE_LIST}" --include TAGS | jq -r --arg TAG "${SERVICE_ROLE_TAG}" '.services|map(.tags = (.tags|from_entries)) | map(select(.tags.role == $TAG ))|map(.serviceName)| if .|length != 1 then halt_error else .[0] end ')

TASK_NAME=$(aws ecs describe-services --cluster "${CLUSTER_NAME}" --services "${SERVICE_NAME}" | jq -r '.services[0].taskDefinition|split("/")[1]|split(":")[0]')

for defn in $(aws ecs list-task-definitions --family-prefix "${TASK_NAME}" --sort ASC | jq -r '.taskDefinitionArns | map(split("/")[1])[]' | head  -n -${KEEP_COUNT}); do
  echo "Degregistering definition $defn"
  aws ecs deregister-task-definition --task-definition "${defn}" >/dev/null
  echo "Removing defintion $defn"
  aws ecs delete-task-definitions --task-definition "${defn}" >/dev/null
  echo "Removed $defn"
  echo
done

echo "Removed old task definitions"
