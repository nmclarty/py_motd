import logging
from argparse import ArgumentParser
from pathlib import Path
from subprocess import run

from ruamel.yaml import YAML

from .Snapshot import Snapshot, SnapshotManager


def main() -> None:
    # cli configuration
    parser = ArgumentParser()
    parser.add_argument(
        "-c", "--config", help="Path to the configuration file", required=True
    )
    parser.add_argument(
        "-l", "--log-level", help="The logging level (verbosity) to use", default="INFO"
    )
    args = parser.parse_args()

    # load the config file
    yaml = YAML()
    config = yaml.load(Path(args.config))
    Snapshot.zpool = config["zpool"]
    Snapshot.directory = config["directory"]

    # configure logging
    logging.basicConfig(level=args.log_level)
    logger = logging.getLogger(__name__)

    # create snapshots and backup
    with SnapshotManager(config["datasets"], config["services"]):
        run(["resticprofile", "backup"], check=True)
        logger.info("Finished backup")


if __name__ == "__main__":
    main()
