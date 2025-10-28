#!/usr/bin/bash

# This is a utility script, similar to scripts/container.exec.bash . Use it to
# run a command in a remote container, either worker or web.

# Give the script two or more parameters. The first is the word "web" or the
# word "worker".  The remainder comprise the command to run including any
# parameters. The command can be quoted as a string or not, as per the
# developer's preference.
#
# e.g.
# ./scripts/aws-container-exec.bash web "echo test"
# or
# ./scripts/aws-container-exec.bash web echo test

set -ex

role="$1"; shift
cmd=$*

if ! [[ "$role" =~ ^(web|worker)$ ]]; then
        echo "Given role was not recognised: $role"
        exit 1
fi

CLUSTER=$(aws ecs list-clusters | jq -r  .clusterArns[0])
mapfile -t TASK_LIST < <(aws ecs list-tasks --cluster "${CLUSTER}" | jq -r .taskArns[])


# Pick one of the web containers
remote_exec=$(aws ecs describe-tasks --include TAGS --cluster "${CLUSTER}" --tasks "${TASK_LIST[@]}" | jq --arg CMD "${cmd}" --arg ROLE "${role}" -r '.tasks|map({arn: .containers[].taskArn, role: .overrides.containerOverrides[].name}) | map(select(.role == $ROLE))[0].arn|split("/") | "aws ecs execute-command --cluster " + .[1] + " --command \"" + $CMD + "\" --interactive --task " + .[2] + " --container ${role}"')
eval "${remote_exec}"
