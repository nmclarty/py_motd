from argparse import ArgumentParser
from pathlib import Path
from subprocess import run
from json import loads

from pystemd.systemd1 import Manager
from ruamel.yaml import YAML

def cleanup(dir: str, zpool: str, dataset: str) -> None:
    if (mount := Path(f"{dir}/{dataset}")).is_mount():
        run(["unmount", mount], check=True)

    ds = f"{zpool}/{dataset}@backup"
    if run(["zfs", "list", ds]).returncode == 0:
        run(["zfs", "destroy", ds], check=True)

def snapshot(dir: str, zpool: str, dataset: str) -> None:
    ds = f"{zpool}/{dataset}@backup"
    run(["zfs" "snapshot", ds], check=True)
    run(["mount", "-t", "zfs", ds, f"{dir}/{dataset}"])

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

    # load systemd manager
    manager = Manager(_autoload=True)

    # stop each service for snapshotting
    for service in config["services"]:
        manager.Manager.StopUnit(bytes(str(service), "utf-8"), b'replace')

    # create temporary snapshots for backups
    for dataset in config["datasets"]:
        cleanup(config["dir"], config["zpool"], dataset)
        snapshot(config["dir"], config["zpool"], dataset)

    # start each service after snapshotting
    for service in config["services"]:
        manager.Manager.StartUnit(bytes(str(service), "utf-8"), b'replace')

    # # run backups
    # run(
    #     ["resticprofile" "remote.backup"],
    #     capture_output=True,
    #     text=True,
    #     check=True,
    # )

    # clean up temporary snapshots for backups
    for dataset in config["datasets"]:
        cleanup(config["dir"], config["zpool"], dataset)

if __name__ == "__main__":
    main()
