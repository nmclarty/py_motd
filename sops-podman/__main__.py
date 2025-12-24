from pathlib import Path

from podman import PodmanClient
from ruamel.yaml import YAML


def flatten(d: dict, parent: str = "", sep: str = "__") -> dict:
    items = {}
    for k, v in d.items():
        new_key = f"{parent}{sep}{k}" if parent else k
        if isinstance(v, dict):
            items.update(flatten(v, new_key, sep=sep))
        else:
            items[new_key] = v
    return items


def main() -> None:
    yaml = YAML()
    secret_file = Path("data/podman.yaml")
    with secret_file.open(encoding="utf-8") as file:
        secrets = yaml.load(file)

    # print(flatten(secrets))

    with PodmanClient() as client:
        if client.ping():
            secrets = client.secrets.list()
            for secret in secrets:
                print(secret)


if __name__ == "__main__":
    main()
