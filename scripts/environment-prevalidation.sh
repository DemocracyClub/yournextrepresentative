#!/usr/bin/env bash

echo Checking for required commands
needed_commands=(aws jq)
for tool in "${needed_commands[@]}"; do
        echo -n "Looking for ${tool}..."
        if ! which "${tool}" > /dev/null; then
                echo "ERROR: Required command ${tool} not found. Please install it or add it to the \$PATH"
                exit 1
        fi
        echo "found"
done
echo "All required commands found"

echo -n "Checking aws-cli authentication..."
if ! aws iam list-users >/dev/null 2>&1 ; then
        if ! [[ -f ~/.aws/credentials ]] ; then
                echo "Could not authenticate with AWS. Please set up your ~/.aws.credentials file"
                exit 1
        fi

        if [ -z "${AWS_PROFILE}" ]; then
                echo "Could not authenticate with AWS. Please re-run this script with AWS_PROFILE defined"
                exit 1
        fi
        echo "Could not authenticate with AWS but could not determine why"
        exit 1
fi
echo OK

# We don't need to check here for the standard tags on the CDK infra for two reasons
# 1) The CDK code creates the tags
# 2) The CDK infra might not have been created yet
# But we do check for the tags on the RDS database, if it exists in the default VPC
echo Getting the Default VPC ID
if ! DEFAULT_VPC_ID=$(aws ec2 describe-vpcs | jq -r '.Vpcs|map(select(.IsDefault == true))[0].VpcId'); then
        echo "Could not get default VPC"
        exit 1
fi
echo VPC ID is "${DEFAULT_VPC_ID}"
echo

echo Checking for a single RDS instance
if ! INSTANCE_COUNT=$(aws rds describe-db-instances | jq -r --arg VPC_ID "${DEFAULT_VPC_ID}"  '.DBInstances |map(select(.DBSubnetGroup.VpcId!=$VPC_ID)) |length'); then
        echo "Could not get RDS instance info"
        exit 1
fi
if [[ ${INSTANCE_COUNT} -ne 1 ]]; then
        echo "WARNING: Expected exactly one RDS instance. Found {$INSTANCE_COUNT}. Unable to perform tag checks"
else
        echo OK: Found exactly 1 RDS instance in the VPC
        echo Getting RDS instance tag info
        JSON=$(aws rds describe-db-instances | jq -r --arg VPC_ID "${DEFAULT_VPC_ID}" '.DBInstances |map(select(.DBSubnetGroup.VpcId==$VPC_ID)) | map({instance: .DBInstanceIdentifier, tags: .TagList|from_entries})[0]')

        echo Looking for dc-environment tag
        if ! echo "${JSON}" | jq -r '.tags.["dc-environment"] | if . == null then halt_error end '; then
                echo ERROR: Tag not found
                exit 1
        fi

        echo Looking for dc-product tag
        if ! echo "${JSON}" | jq -r '.tags.["dc-product"] | if . == null then halt_error end '; then
                echo ERROR: Tag not found
                exit 1
        fi
fi

echo "All checks passed"
