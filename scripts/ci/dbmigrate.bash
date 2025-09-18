#!/usr/bin/bash

set -ex

curl "https://s3.amazonaws.com/session-manager-downloads/plugin/latest/ubuntu_64bit/session-manager-plugin.deb" -o "/tmp/session-manager-plugin.deb"
sudo dpkg -i /tmp/session-manager-plugin.deb
sudo apt update
sudo apt install -y expect

CLUSTER=$(aws ecs list-clusters | jq -r  .clusterArns[0])
mapfile -t TASK_LIST < <(aws ecs list-tasks --cluster "${CLUSTER}" | jq -r '.taskArns[]')

# Pick one of the web containers
aws ecs describe-tasks --include TAGS --cluster "${CLUSTER}" --tasks "${TASK_LIST[@]}" | jq -r '.tasks|map({arn: .containers[].taskArn, role: .overrides.containerOverrides[].name}) | map(select(.role == "web"))[0].arn|split("/") | "unbuffer aws ecs execute-command --cluster " + .[1] + " --command \"python manage.py migrate && python manage.py createcachetable && python manage.py setup_periodic_tasks\" --interactive --task " + .[2]' | sh
