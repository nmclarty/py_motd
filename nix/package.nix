{ pkgs, inputs, ... }:
let
  project = inputs.pyproject-nix.lib.project.loadPyproject {
    projectRoot = ../.;
  };
  python = pkgs.python3;
  attrs = project.renderers.buildPythonPackage { inherit python; };
in
python.pkgs.buildPythonPackage attrs
