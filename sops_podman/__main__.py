"""Simple tool for loading secrets from a YAML file to podman."""

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
    yaml = YAML()

    with PodmanClient() as client:
        if client.ping():
            current_secrets = client.secrets.list()
            print(f"Removing {len(current_secrets)} secrets from podman store...")
            for s in current_secrets:
                s.remove()

            secrets = __flatten(yaml.load(Path("data/podman.yaml")))
            print(f"Adding {len(secrets)} secrets to podman store...")
            for key, val in secrets.items():
                client.secrets.create(key, val)


if __name__ == "__main__":
    main()
