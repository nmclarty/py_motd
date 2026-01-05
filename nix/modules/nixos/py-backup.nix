{ lib, pkgs, perSystem, config, ... }:
with lib;
let
  cfg = config.services.py-backup;
in
{
  options.services.py-backup = {
    enable = mkEnableOption "Enable system backup services.";
    settings = {
      services = mkOption {
        type = types.listOf types.str;
        default = [ ];
        description = "A list of systemd services to be stopped for snapshotting.";
      };

      zpool = mkOption {
        type = types.str;
        description = "The zpool that contains all the datasets to be backed up.";
      };
      datasets = mkOption {
        type = types.listOf types.str;
        default = [ ];
        description = "A list of zfs datasets that will be backed up.";
      };

      dir = mkOption {
        type = types.str;
        default = "/.backup";
        description = "The directory that snapshots will be mounted into for backup.";
      };
    };
  };
  config = mkIf true {
    systemd = {
      tmpfiles.rules = [
        "d ${cfg.settings.dir}"
      ];
      services.backup = {
        description = "Snapshot disks and backup";
        after = [ "network-online.target" ];
        requires = [ "network-online.target" ];
        serviceConfig.ExecStart = "${perSystem.nix-helpers.default}/bin/py_backup -c ${(pkgs.formats.yaml { }).generate "config.yaml" cfg.settings}";
      };
    };
  };
}
