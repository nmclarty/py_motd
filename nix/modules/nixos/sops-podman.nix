{ lib, config, ... }:
with lib;
let
  cfg = config.programs.sops-podman;
in
{
  options.services.sops-podman = {
    enable = mkEnableOption "Enable loading sops secrets to podman.";
  };
  config = mkIf cfg.enable {
    systemd.services.podman-secrets = {
      description = "Load system managed secrets into the podman secret store";
      before = [ "network-online.target" ];
      wantedBy = [ "network-online.target" ];
      serviceConfig = {
        ExecStart = "${perSystem.nix-helpers.default}/bin/sops-podman";
      };
    };
  };
}
