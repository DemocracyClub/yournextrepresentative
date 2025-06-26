#!/usr/bin/bash

set -ex

curl "https://s3.amazonaws.com/session-manager-downloads/plugin/latest/ubuntu_64bit/session-manager-plugin.deb" -o "/tmp/session-manager-plugin.deb"
sudo dpkg -i /tmp/session-manager-plugin.deb
sudo apt update
sudo apt install -y expect
aws ecs list-tasks --cluster "$(aws ecs list-clusters | jq -r  .clusterArns[0])" | jq -r '.taskArns[0]|split("/")| "unbuffer aws ecs execute-command --cluster " + .[1] + " --command \"python manage.py migrate\" --interactive --task " + .[2]' | sh
