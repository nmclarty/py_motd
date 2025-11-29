"""MOTD module for backup status."""

from datetime import datetime
from json import load
from pathlib import Path


class Backup:
    """MOTD module to show information about resticprofile backup status."""

    def __init__(self, module_config: dict[str, str]) -> None:
        """Initialize the backup module."""
        self.config = {
            "status_path": module_config["status_path"],
            "profiles": module_config["profiles"],
        }

        self.profiles = [
            self.__parse_profile(name)
            for name in self.config["profiles"]
            if self.__get_profile_path(name).exists()
        ]

    def __get_profile_path(self, name: str) -> Path:
        """Generate a Path for the status file of a resticprofile backup.

        :param name: The name of the profile
        :return: The Path to the status file
        """
        return Path(f"{self.config['status_path']}/{name}.status")

    def __parse_profile(self, name: str) -> tuple[str, str]:
        """Parse a resticprofile status file to calculate its age.

        :param name: The name of the profile
        :return: A tuple containing the profile name and its age
        """
        with self.__get_profile_path(name).open() as file:
            data = load(file)

        profile = data["profiles"][name]["backup"]
        age = datetime.now() - datetime.fromisoformat(profile["time"]).replace(
            tzinfo=None,
        )
        return (
            name,
            str(age)[:-7],
        )

    def get(self) -> list[dict[str, str]] | dict[str, str]:
        """Return the formatted output of the module.

        :return: The module output
        """
        return [{name: age} for name, age in self.profiles]
