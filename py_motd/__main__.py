import argparse
from os import path
import io
from ruamel.yaml import YAML
from rich.console import Console
from rich.text import Text 

from .modules.backup import Backup
from .modules.update import Update

def main():
    # cli configuration
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", help="Path to the configuration file", default="config.yaml")
    args = parser.parse_args()

    yaml = YAML()
    yaml.indent(mapping=2, sequence=4, offset=2)
    with open(args.config, "r") as config_file:
        config = yaml.load(config_file)

    modules = {
        "Updates": Update(config["update"]).get(),
        "Backups": Backup(config["backup"]).get(),
    }

    console = Console()
    s = io.StringIO()
    yaml.dump(modules, s)
    console.print(s.getvalue())


if __name__ == "__main__":
    main()
