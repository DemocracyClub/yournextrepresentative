#!/usr/bin/env bash

echo "Validating AWS configuration prior to building/updating the environment"

# Though we use the CDK to create a stack and manage the infra therein, there
# are a couple of things which we need to have in place before doing that. One
# example is the database (which can be, but need not be in the same VPC), and
# another being values in the parameter store in order to authenticate with the
# app database.
needed_params=(
    "YNR_AWS_S3_MEDIA_BUCKET" "YNR_AWS_S3_SOPN_REGION"
    "YNR_AWS_S3_SOPN_BUCKET" "YNR_AWS_S3_MEDIA_REGION"
    "DJANGO_SETTINGS_MODULE" "postgres_username" "postgres_host" "postgres_password"
)

for param in "${needed_params[@]}"; do
        echo -n "Checking param store for ${param}..."
        if ! aws ssm get-parameter --name "${param}" > /dev/null ; then
                echo "ERROR: Value not found in parameter store."
                exit 1
        fi
        echo "OK"
done

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
