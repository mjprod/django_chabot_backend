from pathlib import Path

import boto3

def load_parameters():
    try:
        # Initialize SSM client
        ssm_client = boto3.client("ssm", region_name="ap-southeast-2")

        # Get parameter by path
        parameter_path = "/staging_env_details"

        try:
            response = ssm_client.get_parameter(
                Name=parameter_path, WithDecryption=False
            )

            # Parse the parameter value which contains multiple lines
            parameter_value = response["Parameter"]["Value"]

            # Split the value into individual lines
            env_vars = parameter_value.split("\n")

            # Create .env content
            env_content = []
            for line in env_vars:
                if line.strip() and "=" in line:
                    env_content.append(line.strip())

            # Write to .env file
            env_path = Path(__file__).parent / ".env"
            with open(env_path, "w") as env_file:
                env_file.write("\n".join(env_content))

            print(f"Successfully loaded parameters into {env_path}")

        except ssm_client.exceptions.ParameterNotFound:
            print(f"Parameter {parameter_path} not found")
            raise

    except Exception as e:
        print(f"Error loading parameters: {e}")
        raise


if __name__ == "__main__":
    load_parameters()
