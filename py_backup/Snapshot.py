from logging import getLogger
from pathlib import Path
from subprocess import run


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

        check_exists = run(["zfs", "list", self.name], check=False, capture_output=True)
        if check_exists.returncode == 0:
            run(["zfs", "destroy", self.name], check=True)

    def snapshot(self) -> None:
        """Create and mount this snapshot."""
        run(["zfs", "snapshot", self.name], check=True)

        if not self.path.exists():
            self.path.mkdir()
        run(["mount", "-t", "zfs", self.name, self.path], check=True)


class SnapshotManager:
    """Manages a collection of ZFS snapshots, creating and then cleaning them up when finished."""

    logger = getLogger(__name__)

    def __init__(self, datasets: list[str], services: list[str]):
        self.snapshot = [Snapshot(name) for name in datasets]
        self.services = services

    def __enter__(self):
        # stop all the services before
        if len(self.services) != 0:
            run(["systemctl", "stop", *self.services], check=True)
            self.logger.info("Stopped services")

        for s in self.snapshot:
            s.cleanup()
            s.snapshot()
        self.logger.info("Created temporary snapshots")

        # create long-term snapshots for local recovery
        run(["systemctl", "start", "sanoid.service"], check=True)
        self.logger.info("Created long-term snapshots")

        # start all the services after
        if len(self.services) != 0:
            run(["systemctl", "start", *self.services], check=True)
            self.logger.info("Started services")

        return self

    def __exit__(self, exc_type, exc_value, exc_tb) -> None:
        for s in self.snapshot:
            s.cleanup()
        self.logger.info("Cleaned up snapshots")
