"""Main entry point for py_motd."""

from argparse import ArgumentParser
from io import StringIO
from pathlib import Path

from rich.console import Console
from ruamel.yaml import YAML

from .modules.backup import Backup
from .modules.update import Update


def main() -> None:
    """Run the main py_motd app."""
    # cli configuration
    parser = ArgumentParser()
    parser.add_argument(
        "-c",
        "--config",
        help="Path to the configuration file",
        default="~/.config/py_motd/config.yaml",
    )
    args = parser.parse_args()

    # load the config file
    yaml = YAML()
    yaml.indent(mapping=2, sequence=4, offset=2)
    config_file = Path(args.config).expanduser()
    with config_file.open() as file:
        config = yaml.load(file)

    # initialize and then run each module
    modules = {
        "Updates": Update(config["update"]).get(),
        "Backups": Backup(config["backup"]).get(),
    }

    # output each module's result as yaml
    console = Console()
    s = StringIO()
    yaml.dump(modules, s)
    console.print(s.getvalue())


if __name__ == "__main__":
    main()
