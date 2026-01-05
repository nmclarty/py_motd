from argparse import ArgumentParser
from pathlib import Path
from subprocess import run

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

        self.path.mkdir()
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

    # stop each service before snapshotting
    if len(services := config["services"]) != 0:
        run(["systemctl", "stop"] + services, check=True)
        print("Stopped services")

    # create temporary snapshots for backups
    for s in snapshot:
        s.cleanup()
        s.snapshot()
    print("Created temporary snapshots")

    # create long-term snapshots for local recovery
    run(["systemctl", "start", "sanoid.service"], check=True)
    print("Created long-term snapshots")

    # start each service after snapshotting
    if len(services := config["services"]) != 0:
        run(["systemctl", "start"] + services, check=True)
        print("Started services")

    # run backups
    run(["resticprofile", "backup"], check=True)
    print("Finished backup")

    # clean up temporary snapshots for backups
    for s in snapshot:
        s.cleanup()
    print("Cleaned up snapshots")


if __name__ == "__main__":
    main()
