import os
from pathlib import Path

import boto3


def load_parameters():
    try:
        # Initialize SSM client
        ssm_client = boto3.client("ssm", region_name="ap-southeast-2")

        # Define your parameter path prefix
        parameter_path = "/staging_env_details"  # Example: /chatbot/prod/

        # Get all parameters under the path
        paginator = ssm_client.get_paginator("get_parameters_by_path")
        parameters = []

        for page in paginator.paginate(
            Path=parameter_path, Recursive=True, WithDecryption=True
        ):
            parameters.extend(page["Parameters"])

        # Create .env content
        env_content = []
        for param in parameters:
            # Extract parameter name (last part of the path)
            param_name = param["Name"].split("/")[-1]
            param_value = param["Value"]
            env_content.append(f"{param_name}={param_value}")

        # Write to .env file
        env_path = Path(__file__).parent / ".env"
        with open(env_path, "w") as env_file:
            env_file.write("\n".join(env_content))

        print("Successfully loaded parameters into .env file")

    except Exception as e:
        print(f"Error loading parameters: {e}")


if __name__ == "__main__":
    load_parameters()
