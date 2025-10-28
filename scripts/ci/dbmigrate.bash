#!/usr/bin/bash

set -euxo pipefail

curl "https://s3.amazonaws.com/session-manager-downloads/plugin/latest/ubuntu_64bit/session-manager-plugin.deb" -o "/tmp/session-manager-plugin.deb"
sudo dpkg -i /tmp/session-manager-plugin.deb
sudo apt update
sudo apt install -y expect

CLUSTER=$(aws ecs list-clusters | jq -r  .clusterArns[0])
mapfile -t TASK_LIST < <(aws ecs list-tasks --cluster "${CLUSTER}" | jq -r '.taskArns[]')

# Find the web task
read -r _ CLUSTER_NAME TASK_ID < <(
  aws ecs describe-tasks --include TAGS \
    --cluster "${CLUSTER}" \
    --tasks "${TASK_LIST[@]}" \
  | jq -r '.tasks
            | map({arn: .containers[].taskArn, role: .overrides.containerOverrides[].name})
            | map(select(.role == "web"))[0].arn
            | split("/") 
            | @tsv'
)

# We have to do a bit of a silly dance to see if these jobs worked or not
# https://github.com/aws/amazon-ecs-agent/issues/2846

MIGRATE_OUTPUT=$(unbuffer aws ecs execute-command --cluster "${CLUSTER_NAME}" --task "${TASK_ID}" --container web --interactive --command "sh -c 'python manage.py migrate && echo SUCCESS'" 2>&1)
echo "$MIGRATE_OUTPUT"
if echo "$MIGRATE_OUTPUT" | grep -q 'SUCCESS'; then
  echo "✔ Migrations applied"
else
  echo "✖ Migrations failed"
  exit 1
fi

CACHE_OUTPUT=$(unbuffer aws ecs execute-command --cluster "${CLUSTER_NAME}" --task "${TASK_ID}" --container web --interactive --command "sh -c 'python manage.py createcachetable && echo SUCCESS'"2>&1)
echo "$CACHE_OUTPUT"
if echo "$CACHE_OUTPUT" | grep -q 'SUCCESS'; then
    echo "✔ Cache table created"
else
    echo "✖ Cache table creation failed"
    exit 1
fi

TASKS_OUTPUT=$(unbuffer aws ecs execute-command --cluster "${CLUSTER_NAME}" --task "${TASK_ID}" --container web --interactive --command "sh -c 'python manage.py setup_periodic_tasks && echo SUCCESS'"2>&1)
echo "$TASKS_OUTPUT"
if echo "$TASKS_OUTPUT" | grep -q 'SUCCESS'; then
    echo "✔ Periodic tasks updated"
else
    echo "✖ Periodic tasks setup failed"
    exit 1
fi
