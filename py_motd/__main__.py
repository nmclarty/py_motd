"""Main entry point for py_motd."""

from argparse import ArgumentParser
from importlib import import_module
from io import StringIO
from pathlib import Path

from rich.console import Console
from ruamel.yaml import YAML


def __run_modules(modules: list[str], config: dict) -> dict:
    output = {}
    for name in [n for n in modules if config[n] and config[n]["enable"]]:
        c = getattr(import_module(f"{__package__}.modules.{name}"), name.capitalize())
        output[c.display_name] = c(config[name]).get()
    return output


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
    parser.add_argument(
        "-m",
        "--modules",
        type=lambda i: i.split(","),
        help="List of modules to run, and their order (comma separated).",
        default="update,backup",
    )
    args = parser.parse_args()

    # load the config file
    yaml = YAML()
    yaml.indent(sequence=4, offset=2)
    config = yaml.load(Path(args.config).expanduser())

    # output the combined result of each module
    console = Console()
    s = StringIO()
    yaml.dump(__run_modules(args.modules, config), s)
    console.print(s.getvalue())


if __name__ == "__main__":
    main()
