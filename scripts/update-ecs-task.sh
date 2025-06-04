#!/usr/bin/bash

set -ex

IMAGE_NAME=ynr
CLUSTER_APP_TAG=ynr
SERVICE_ROLE_TAG=web
REGION=eu-west-2
IMAGE_TAG=$1
shift


REPO="public.ecr.aws/h3q9h5r7/dc-test"
echo "Using Repo: ${REPO}, Image: ${IMAGE_NAME}, Tag: ${IMAGE_TAG}"

CLUSTER_LIST=$(aws ecs list-clusters | jq -r '.clusterArns|map(split("/")[1])[]')

# Force an error if we have a count of matching clusters that differs from 1
CLUSTER_NAME=$(aws ecs describe-clusters --include TAGS --cluster "${CLUSTER_LIST}" | jq -r --arg TAG "${CLUSTER_APP_TAG}" '.clusters|map(.tags = (.tags|from_entries)) | map(select(.tags.app == $TAG and  .status == "ACTIVE" ))|map(.clusterName)| if .|length != 1 then halt_error else .[0] end ')
SERVICE_LIST=$(aws ecs list-services  --cluster "${CLUSTER_NAME}" | jq -r '.serviceArns|map(split("/")[2])[]')

# Force an error if we have a count of matching services that differs from 1
SERVICE_NAME=$(aws ecs describe-services  --cluster "${CLUSTER_NAME}" --service "${SERVICE_LIST}" --include TAGS | jq -r --arg TAG "${SERVICE_ROLE_TAG}" '.services|map(.tags = (.tags|from_entries)) | map(select(.tags.role == $TAG ))|map(.serviceName)| if .|length != 1 then halt_error else .[0] end ')

NEW_IMAGE="${REPO}/$IMAGE_NAME:$IMAGE_TAG"
TASK_NAME=$(aws ecs describe-services --cluster "${CLUSTER_NAME}" --services "${SERVICE_NAME}" | jq -r '.services[0].taskDefinition|split("/")[1]|split(":")[0]')
TASK_DEFINITION=$(aws ecs describe-task-definition --task-definition "$TASK_NAME" --region "$REGION")
NEW_TASK_DEFINITION=$(echo "$TASK_DEFINITION" | jq --arg IMAGE "$NEW_IMAGE" '.taskDefinition | .containerDefinitions[0].image = $IMAGE | del(.taskDefinitionArn) | del(.revision) | del(.status) | del(.requiresAttributes) | del(.compatibilities) | del(.registeredAt) | del(.registeredBy)')
NEW_REVISION=$(aws ecs register-task-definition --region "$REGION" --cli-input-json "$NEW_TASK_DEFINITION")
NEW_REVISION_DATA=$(echo "$NEW_REVISION" | jq '.taskDefinition.revision')

aws ecs update-service --cluster "$CLUSTER_NAME" --service "$SERVICE_NAME" --task-definition "$TASK_NAME" --force-new-deployment

echo "done"
echo "${TASK_NAME}, Revision: ${NEW_REVISION_DATA}, Image: ${NEW_IMAGE}"
