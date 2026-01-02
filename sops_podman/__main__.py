"""Simple tool for loading secrets from a YAML file to podman."""

import sys
from argparse import ArgumentParser
from pathlib import Path

from podman import PodmanClient
from ruamel.yaml import YAML


def __flatten(d: dict, parent: str = "", sep: str = "__") -> dict:
    items = {}
    for k, v in d.items():
        new_key = f"{parent}{sep}{k}" if parent else k
        if isinstance(v, dict):
            items.update(__flatten(v, new_key, sep=sep))
        else:
            items[new_key] = v
    return items


def main() -> None:
    """Run the main sops_podman utility."""
    # cli configuration
    parser = ArgumentParser()
    parser.add_argument(
        "-s", "--secret-file", help="Path to the secret file", required=True
    )
    parser.add_argument(
        "-p",
        "--podman-connection",
        help="The podman connection string",
        required=True,
    )
    args = parser.parse_args()
    yaml = YAML()

    with PodmanClient(base_url=args.podman_connection) as client:
        try:
            if not client.ping():
                raise Exception("Client ping didn't respond with OK")
        except Exception as e:
            print(f"Error connecting to Podman: {e}", file=sys.stderr)
            sys.exit(1)

        current_secrets = client.secrets.list()
        print(f"Removing {len(current_secrets)} secrets from podman store...")
        for s in current_secrets:
            s.remove()

        secrets = __flatten(yaml.load(Path(args.secret_file)))
        print(f"Adding {len(secrets)} secrets to podman store...")
        for key, val in secrets.items():
            client.secrets.create(key, bytes(str(val), "utf-8"))


if __name__ == "__main__":
    main()
