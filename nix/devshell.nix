{ pkgs }:
let
  pythonPkgs = with pkgs.python313Packages; [
    # py-motd
    ruamel-yaml
    rich
    # sops-podman
    podman
    # py-backup
    pystemd
  ];
in
pkgs.mkShell {
  packages = with pkgs; [
    python313
    ruff
  ] ++ pythonPkgs;

  env = { };

  shellHook = ''

  '';
}
