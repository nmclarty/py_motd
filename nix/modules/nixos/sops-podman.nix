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
        types = types.str;
        description = "The path the the encrypted sops file to be loaded from.";
      };
    };
  };
  config = mkIf cfg.enable {
    sops.secrets."sops-podman.yaml" = {
      restartUnits = [ "sops-podman.service" ];
      sopsFile = cfg.settings.sopsFile;
      key = "";
    };
    systemd.services.sops-podman = {
      description = "Load system managed secrets into the podman secret store";
      before = [ "network-online.target" ];
      wantedBy = [ "network-online.target" ];
      serviceConfig = {
        ExecStart = "${perSystem.nix-helpers.default}/bin/sops_podman ${cfg.sops.secrets."sops-podman.yaml".path}";
      };
    };
  };
}
