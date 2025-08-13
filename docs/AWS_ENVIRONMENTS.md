# Description

This document explains how the AWS environments are configured and attempts to
identify (where relevant) the sequencing of events and resources, and which of
these are manual and which are automated.

The Democracy Club convention is to have one AWS account per app per
environment insofar as is possible, and we follow that convention for this app.
One outlier which is worthy of mention is the Development account, which also
holds the public container registry.

# CI Deploy user
Note: This section is written with the assumption that we use CircleCI for
deployments.

* Authenticate with the CircleCI web interface and create a context
for the environment. Ideally use a name of the form
`deployment-ecs-development-ynr`, replacing the penultimate component with the
environment name.
* In the AWS web console, create an IAM User called `CircleCIDeployer`
(https://us-east-1.console.aws.amazon.com/iam/home?region=eu-west-2#/users).
* Create an access key / token pair for this user and add it to the CircleCI
context for the YNR app in this environment.
* Create a UserGroup called CircleCIDeployer and add the user you've just
created to that group.
* Add the following permission policies to that UserGroup:
  * `AmazonEC2ContainerRegistryFullAccess`
  * `AmazonECS_FullAccess`
  * `AmazonElasticContainerRegistryPublicFullAccess`
  * `AmazonS3FullAccess`
  * `AmazonSSMFullAccess`
  * `AmazonVPCReadOnlyAccess`
  * `AWSCloudFormationFullAccess`
  * `IAMFullAccess`

Note that you'll need to do this for each new environment / AWS account.

# VPC

Because we have an AWS account on a per-app, per-environment basis, we are able
to use the default VPC to hold the relevant infrastructure.

# Shared Docker Registry

We use AWS Elastic Container Registry Public to host the container images. We
use the same registry for each environment, intentionally so, such that we can
be confident the same image will be promoted between environments.

At the time of writing the registry is in the account used by the development
environment. If it gets moved to another account then some likely steps will be:

* Create a context in which there are variables exposed containing AWS access credentials for the correct account.
* Add this CircleCI context to the .circleci/config.yml file in the workflows calling jobs which perform the docker push/tag operations.

# Database creation

The database is intentionally managed outside of the stack automation, such
that the database remains in the event of stack deletion.

The simplest approach (from a networking point of view) is to create the RDS
instance where the app will be, i.e. inside the default VPC.  If you create the
database elsewhere (or perhaps have an existing database but wish to create a
CDK-driven application layer) then you will need to configure VPC peering and
ensure that there are relevant security group rules to allow the app to connect.

Here is the recommended RDS configuration:
* Size: t3 Micro
* Single AZ
* Name: `ynr-environment-db` (e.g. `ynr-development-db`)
* Engine: 16.8
* Option group: default
* 1G RAM, 2 vCPUs
* Storage: gp3, 20G, 3000 iops
* Master username: postgres
* Public access: Yes
* VPC: Default
* Security group: Create a new one with the name `ynr-development-db` (or `staging` or `production`)
* Add the customary Democracy club tags of: `dc-product`: `ynr` and `dc-environment`: `development` (or `staging` or `production`)

The reason for public internet access is that it allows developers to perform
investigation and diagnostic operations. But note that though the instance is
theoretically open, security group rules are used to keep access tight.

The recommended security group rules are as follows:

* Port 5432, address range 172.31.0.0/16, Description: Application (NB the default VPC uses this address space whereas user-created VPC typically use 10.0.0.0/16)
* Plus rule(s) for individual developer home IP addresses. Give any such rules a sensible description, in order to make it easier to keep these rules pruned.

You will need to connect to the database and either import a dump file or
manually create a postgres role (called e.g. `djangouser`) for the application and then a database owned
by that role (called e.g. `ynr`)

# Parameter store

Add parameter store (https://eu-west-2.console.aws.amazon.com/systems-manager/parameters)
entries for required env vars.

# Pre-build environment validation

Not yet as part of the CI, but there is a convenience script to be run locally
from a development machine: `scripts/environment-prevalidation.sh`

This performs a series of lightweight read-only operations on the AWS
environment to help identify possible configuration issues *prior to the
initial build*.

It uses the `aws` CLI tool, so if you have multiple credential sets in
`~/.aws/credentials` then you can set the environment variable `AWS_PROFILE` to
select the correct one. E.g.

```shell
AWS_PROFILE=staging ./scripts/environment-prevalidation.sh
```


# Environment build / update

Initial build and update are done in the same way as each other.

Deployments go to an environment depending on the branch name being used.

* `ci/test` - this goes to the development environment.
* `staging` - this goes to the staging environment.


# Domains and certificates 

For each new environment we need to manually create a hosted zone that 
matches the `FQDN` value in the parameter store. 

This domain needs an ACM certificate to be manually created in the `us-east-1` 
region. Once created, add the ARN against the environment to the `cert_arns` 
dict in cdk/stack/ynr.py.

A new deployment will create a CloudFront distribution and set up the 
required DNS. 
