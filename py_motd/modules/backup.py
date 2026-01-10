"""MOTD module for backup status."""

from datetime import datetime
from json import load
from json.decoder import JSONDecodeError
from pathlib import Path


def sizeof_fmt(num: float, suffix="B") -> str:
    """Parse a number (of bytes) and return a human-readable version.

    :param num: The number to parse.
    :return: A string of the formatted number.
    """
    for unit in ("", "K", "M", "G", "T", "P", "E", "Z"):
        if abs(num) < 1000.0:
            return f"{num:3.1f} {unit}{suffix}"
        num /= 1000.0
    return f"{num:.1f} Y{suffix}"


def parse_status(status: dict) -> dict[str, str]:
    """Parse a resticprofile status file to calculate details.

    :param status: A dict containing the unprocessed file.
    :return: A tuple containing the profile name and its age.
    """

    backup = status["profiles"]["default"]["backup"]
    return {
        "status": "Success" if backup["success"] else backup["error"],
        "age": str(
            datetime.now() - datetime.fromisoformat(backup["time"]).replace(tzinfo=None)
        ),
        "added": sizeof_fmt(backup["bytes_added"]),
        "total": sizeof_fmt(backup["bytes_total"]),
    }


class Backup:
    """MOTD module to show information about resticprofile backup status."""

    display_name = "Backup"

    def __init__(self, module_config: dict[str, str]) -> None:
        """Initialize the backup module."""
        self.config = {
            "status_file": module_config["status_file"],
        }

        try:
            with Path(self.config["status_file"]).open() as file:
                self.profile = parse_status(load(file))
        except (FileNotFoundError, JSONDecodeError, KeyError):
            self.profile = None

    def get(self) -> dict[str, str]:
        """Return the formatted output of the module.

        :return: The module output
        """
        if self.profile is not None:
            return {
                "Status": self.profile["status"],
                "Ran": f"{self.profile['age'][:-7]} ago",
                "Added": self.profile["added"],
                "Total": self.profile["total"],
            }
        else:
            return {"Status": "Failed to parse status file"}
