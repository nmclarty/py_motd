"""MOTD module for system updates."""

from datetime import datetime
from json import load, loads
from pathlib import Path
from subprocess import run


class Update:
    """MOTD module to show information about NixOS generations and flake inputs."""

    def __init__(self, module_config: dict) -> None:
        """Initialize the update module and fetches the input files.

        :param module_config: The configuration for the module
        """
        self.config = {
            "source_path": module_config["source_path"],
            "inputs": module_config["inputs"],
            "generation_count": module_config["generation_count"],
        }

        # load the lock file from the flake (source path)
        flake_lock_file = Path(f"{self.config['source_path']}/flake.lock")
        with flake_lock_file.open() as file:
            self.__flake_lock = load(file)["nodes"]

        # iterate over each input defined in the config, then parse it
        self.inputs = [
            self.__parse_input(name)
            for name in self.config["inputs"]
            if name in self.__flake_lock
        ]

        # iterate over the last n generations from nixos-rebuild, and parse them
        self.generations = [
            self.__parse_generation(g)
            for g in loads(
                run(
                    ["nixos-rebuild", "list-generations", "--json"],
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout,
            )[: self.config["generation_count"]]
        ]

        # get the current generation
        self.g = next(g for g in self.generations if g["current"])

    def __parse_input(self, name: str) -> tuple[str, str]:
        """Parse a nix flake input to calculate its age.

        Takes the name of a nix flake input, fetches it from the
        imported flake lockfile, and calculates its age from how long ago
        it was updated.

        :param name: The name of the input
        :return: A tuple containing the input name and its age
        """
        i = self.__flake_lock[name]
        age = datetime.now() - datetime.fromtimestamp(i["locked"]["lastModified"])
        return (
            name,
            str(age)[:-7],
        )

    def __parse_generation(self, g: dict) -> dict:
        """Parse a NixOS generation to calculate its age.

        Takes a nix generation, and calculates the age of how long ago it was
        built, and then adds that to the returned dict.

        :param g: The generation to be parsed
        :return: The generation with the age added
        """
        last_build = datetime.now() - datetime.fromisoformat(g["date"])
        g["age"] = str(last_build)[:-7]
        return g

    def get(self) -> dict:
        """Return the formatted output of the module.

        :return: The module output
        """
        return {
            "Current": {
                "Generation": self.g["generation"],
                "Version": self.g["nixosVersion"],
                "Kernel": self.g["kernelVersion"],
            },
            "History": [{g["generation"]: f"{g['age']} ago"} for g in self.generations],
            "Inputs": [{name: f"{age} ago"} for name, age in self.inputs],
        }
