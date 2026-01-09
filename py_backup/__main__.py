import logging
import sys
from argparse import ArgumentParser
from pathlib import Path
from subprocess import run

from pydantic import BaseModel, ValidationError
from ruamel.yaml import YAML

from .Snapshot import SnapshotManager, ZpoolConfig


class Config(BaseModel):
    services: list[str]
    zpool: ZpoolConfig


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

    # configure logging
    logging.basicConfig(level=args.log_level)
    logger = logging.getLogger(__name__)

    # load the config file
    yaml = YAML()
    try:
        config = Config.model_validate(yaml.load(Path(args.config)))
    except ValidationError as e:
        logger.critical(f"Invalid configuration \n{e}")
        sys.exit(1)

    # create snapshots and backup
    with SnapshotManager(config.zpool, config.services):
        run(["resticprofile", "backup"], check=True)
        logger.info("Finished backup")


if __name__ == "__main__":
    main()
