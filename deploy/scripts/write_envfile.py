import argparse
from typing import Dict, List

import boto3


client = boto3.client("ssm", region_name="eu-west-2")


def get_parameter_store_names(prefix) -> List:
    response = client.describe_parameters(
        Filters=[{"Key": "Name", "Values": [prefix]}], MaxResults=50
    )
    return [param["Name"] for param in response["Parameters"]]


def get_parameter_store_vars(prefix) -> Dict:
    parameters = {}
    names = get_parameter_store_names(prefix)
    for name in names:
        key = name.split("/")[-1]
        if not key.isupper():
            # Env vars should be capitalised.
            continue
        response = client.get_parameter(Name=name)
        value = response["Parameter"]["Value"]
        parameters[key] = value

    return parameters


def write_parameters_to_envfile(prefix) -> None:
    parameter_store_vars = get_parameter_store_vars(prefix)

    with open(".env", "w") as f:
        for key, value in parameter_store_vars.items():
            f.write(f"{key}='{value}'\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--key-prefix", required=True, action="store")
    args = parser.parse_args()

    write_parameters_to_envfile(prefix=args.key_prefix)
