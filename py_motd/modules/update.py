from json import load, loads
from datetime import datetime, timezone, timedelta
from subprocess import run
from sys import argv

def parse_generation(g: dict) -> dict:

    last_build = (
        datetime.now() -
        datetime.fromisoformat(g["date"])
    )

    current = " (current) " if g["current"] else ""

    return {
        "ago": str(last_build)[:-7] + " ago",
        "version": f'{g["generation"]}{current}[{g["nixosVersion"]}] ({g["kernelVersion"]})',
    }

class Update:
    def __init__(self, module_config: dict):
        self.source_path = module_config["source_path"]
        self.inputs = module_config["inputs"]
        self.generation_count = module_config["generation_count"]

        # load the flake lock file
        with open(f"{self.source_path}/flake.lock", "r") as file:
            self.flake_lock = load(file)

        self.generations = loads(run(["nixos-rebuild", "list-generations", "--json"],
                                        capture_output=True, text=True, check=True).stdout)[:self.generation_count]


    def get(self):
        output = {}

        output["Generations"] = []
        for g in map(parse_generation, self.generations):
            output["Generations"].append( { g["version"]: g["ago"] })

        output["Inputs"] = []
        for i in map(self.__calculate_diff, self.inputs):
            output["Inputs"].append({ i[0]: f'{str(i[1])[:-7]} ago'})

        return output
    

    def __calculate_diff(self, input: str) -> list[str | timedelta]:
        """Calculates the time difference between now and the last modified time of
        a nix flake input (i.e. nixpkgs).

        :param input: The nix flake input name to check
        :return: A list containing the input name and the time difference
        """
        then = datetime.fromtimestamp(
            self.flake_lock["nodes"][input]["locked"]["lastModified"])
        return [input, datetime.now() - then]
