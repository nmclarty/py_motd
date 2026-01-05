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
      directory = mkOption {
        type = types.str;
        default = "/.backup";
        description = "The directory that snapshots will be mounted into for backup.";
      };
    };
  };
  config = mkIf true {
    systemd = {
      tmpfiles.rules = [
        "d ${cfg.settings.directory}"
      ];
      services.backup = {
        description = "Snapshot disks and backup";
        after = [ "network-online.target" ];
        requires = [ "network-online.target" ];
        serviceConfig.ExecStart = "${perSystem.nix-helpers.default}/bin/py_backup -c ${(pkgs.formats.yaml { }).generate "config.yaml" cfg.settings}";
      };
      timers.backup = {
        enable = true;
        description = "Run backup daily at 4am";
        wantedBy = [ "timers.target" ];
        timerConfig = {
          OnCalendar = "*-*-* 4:00:00";
          Persistent = true;
        };
      };
    };

    sops = {
      secrets = {
        "restic/password" = { };
        "restic/remote/access" = { };
        "restic/remote/secret" = { };
      };
      templates."resticprofile/profiles.json" = {
        path = "/etc/resticprofile/profiles.json";
        content =
          let
            settings = {
              version = "1";

              default = {
                repository = "s3:${config.private.restic.remote.host}/${config.networking.hostName}-restic";
                password-file = config.sops.secrets."restic/password".path;
                env = {
                  AWS_ACCESS_KEY_ID = config.sops.placeholder."restic/remote/access";
                  AWS_SECRET_ACCESS_KEY = config.sops.placeholder."restic/remote/secret";
                };
                extended-status = true;
                status-file = "/var/lib/resticprofile/status";
                force-inactive-lock = true;
                initialize = true;
                cache-dir = "/var/cache/restic";
                cleanup-cache = true;
                pack-size = 64;
                backup = {
                  tag = "automatic";
                  source = cfg.settings.datasets;
                  source-base = cfg.settings.directory;
                  source-relative = true;
                };
                retention = {
                  after-backup = true;
                  tag = true;
                  prune = true;
                  keep-daily = 7;
                  keep-weekly = 4;
                };
              };
            };
          in
          builtins.toJSON settings;
      };
    };
  };
}
