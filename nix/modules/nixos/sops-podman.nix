{ lib, config, perSystem, ... }:
with lib;
let
  cfg = config.services.sops-podman;
in
{
  options.services.sops-podman = {
    enable = mkEnableOption "Enable loading sops secrets to podman.";
    settings = {
      sopsFile = mkOption {
        type = types.str;
        description = "The path the the encrypted sops file to be loaded from.";
      };
      podmanConnection = mkOption {
        type = types.str;
        default = "unix:///run/podman/podman.sock";
        description = "The podman connection string to use.";
      };
    };
  };
  config = mkIf cfg.enable {
    sops.secrets."sops-podman.yaml" = {
      restartUnits = [ "sops-podman.service" ];
      inherit (cfg.settings) sopsFile;
      key = "";
    };
    system.activationScripts.sops-podman = {
      deps = [ "setupSecrets" ];
      text = ''
        ${perSystem.nix-helpers.default}/bin/sops_podman \
        -s '${config.sops.secrets."sops-podman.yaml".path}' \
        -p '${cfg.settings.podmanConnection}' || true
      '';
    };
  };
}
