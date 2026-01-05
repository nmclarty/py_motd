from argparse import ArgumentParser
from pathlib import Path
from subprocess import run

from pystemd.systemd1 import Manager
from ruamel.yaml import YAML


class Snapshot:
    """Simple class for making operations on a zfs snapshot easier."""

    zpool = None
    directory = None

    def __init__(self, name: str) -> None:
        self.name = f"{Snapshot.zpool}/{name}@backup"
        self.path = Path(f"{Snapshot.directory}/{name}")

    def __str__(self) -> str:
        return f"{self.name}:{self.path}"

    def cleanup(self) -> None:
        """Unmount and destroy this snapshot."""
        if self.path.is_mount():
            run(["umount", self.path], check=True)

        if run(["zfs", "list", self.name], check=False, capture_output=True).returncode == 0:
            run(["zfs", "destroy", self.name], check=True)

    def snapshot(self) -> None:
        """Create and mount this snapshot."""
        run(["zfs", "snapshot", self.name], check=True)
        run(["mount", "-t", "zfs", self.name, self.path], check=True)


def main() -> None:
    # cli configuration
    parser = ArgumentParser()
    parser.add_argument(
        "-c", "--config", help="Path to the configuration file", required=True,
    )
    args = parser.parse_args()

    # load the config file
    yaml = YAML()
    config = yaml.load(Path(args.config))
    Snapshot.zpool = config["zpool"]
    Snapshot.directory = config["directory"]
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

    # run backups
    run(["resticprofile", "backup"], check=True)

    # clean up temporary snapshots for backups
    for s in snapshot:
        s.cleanup()
        print(f"Cleaned up snapshot '{s}'")


if __name__ == "__main__":
    main()
