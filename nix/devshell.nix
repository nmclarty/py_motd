{ pkgs }:
let
  pythonPkgs = with pkgs.python313Packages; [
    ruamel-yaml
    rich
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
