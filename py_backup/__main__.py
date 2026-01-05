from argparse import ArgumentParser
from pathlib import Path
from subprocess import run
from json import loads

from pystemd.systemd1 import Manager
from ruamel.yaml import YAML


class Snapshot:
    zpool = None
    directory = None

    def __init__(self, name: str) -> None:
        self.name = f"{Snapshot.zpool}/{name}@backup"
        self.path = Path(f"{Snapshot.directory}/{name}")

    def __str__(self) -> str:
        return f"{self.name}:{self.path}"

    def cleanup(self) -> None:
        if self.path.is_mount():
            run(["umount", self.path], check=True)

        if run(["zfs", "list", self.name], capture_output=True).returncode == 0:
            run(["zfs", "destroy", self.name], check=True)

    def snapshot(self) -> None:
        run(["zfs", "snapshot", self.name], check=True)
        run(["mount", "-t", "zfs", self.name, self.path])

def main() -> None:
    # cli configuration
    parser = ArgumentParser()
    parser.add_argument(
        "-c", "--config", help="Path to the configuration file", required=True
    )
    args = parser.parse_args()

    # load the config file
    yaml = YAML()
    config = yaml.load(Path(args.config))
    snapshot = [Snapshot(name) for name in config["datasets"]]

    # load systemd manager
    manager = Manager(_autoload=True)

    # stop each service for snapshotting
    for service in config["services"]:
        manager.Manager.StopUnit(bytes(str(service), "utf-8"), b"replace")

    # create temporary snapshots for backups
    for s in snapshot:
        s.cleanup()
        s.snapshot()
        print(f"Created snapshot '{s}'")

    # start each service after snapshotting
    for service in config["services"]:
        manager.Manager.StartUnit(bytes(str(service), "utf-8"), b"replace")

    # # run backups
    # run(
    #     ["resticprofile" "remote.backup"],
    #     capture_output=True,
    #     text=True,
    #     check=True,
    # )

    # clean up temporary snapshots for backups
    for s in snapshot:
        s.cleanup()
        print(f"Cleaned up snapshot '{s}'")


if __name__ == "__main__":
    main()
