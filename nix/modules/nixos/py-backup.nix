{ lib, pkgs, perSystem, config, ... }:
with lib;
let
  cfg = config.services.py-backup;
in
{
  options.services.py-backup = {
    enable = mkEnableOption "Enable system backup services.";
    interval = mkOption {
      type = types.str;
      description = "Run backup services at this interval.";
    };
    settings = {
      services = mkOption {
        type = types.listOf types.str;
        default = [ ];
        description = "A list of systemd services to be stopped for snapshotting.";
      };
      zpool = {
        name = mkOption {
          type = types.str;
          description = "The zpool that contains all the datasets to be backed up.";
        };
        directory = mkOption {
          type = types.str;
          default = "/.backup";
          description = "The directory that snapshots will be mounted into for backup.";
        };
        datasets = mkOption {
          type = types.listOf types.str;
          default = [ ];
          description = "A list of zfs datasets that will be backed up.";
        };
      };
    };
    restic = {
      repository = mkOption {
        type = types.str;
        description = "The repository to use for restic backup.";
      };
      retention = {
        days = mkOption {
          type = types.int;
          description = "The amount of days to keep snapshots and backups for";
        };
        weeks = mkOption {
          type = types.int;
          description = "The amount of weeks to keep snapshots and backups for";
        };
      };
      statusFile = mkOption {
        type = types.str;
        default = "/var/lib/resticprofile/status.json";
        description = "The file where resticprofile's status will be written to.";
      };
    };
  };
  config = mkIf cfg.enable {
    systemd = {
      tmpfiles.rules = [
        "d ${cfg.settings.zpool.directory}"
        "f ${cfg.restic.statusFile}"
      ];
      services = {
        # otherwise starting sanoid with systemd won't wait for completion
        sanoid.serviceConfig.Type = "oneshot";
        backup = {
          description = "Snapshot disks and backup";
          after = [ "network-online.target" "zfs.target" ];
          requires = [ "network-online.target" "zfs.target" ];
          path = with pkgs; [
            zfs
            util-linux
            resticprofile
          ];
          environment.PYTHONUNBUFFERED = "1"; # otherwise stdout is delayed
          serviceConfig = {
            Type = "oneshot";
            ExecStart = "${perSystem.nix-helpers.default}/bin/py_backup -c ${(pkgs.formats.yaml { }).generate "config.yaml" cfg.settings}";
          };
        };
      };
      timers = {
        # since we're triggering sanoid manually, disable its timer
        sanoid.enable = mkForce false;
        backup = {
          enable = true;
          wantedBy = [ "timers.target" ];
          timerConfig = {
            OnCalendar = cfg.interval;
            Persistent = true;
          };
        };
      };
    };

    sops = {
      secrets = {
        "restic/password" = { };
        "restic/access_key" = { };
        "restic/secret_key" = { };
      };
      templates."resticprofile/profiles.json" = {
        path = "/etc/resticprofile/profiles.json";
        content =
          let
            settings = {
              version = "1";

              default = {
                inherit (cfg.restic) repository;
                password-file = config.sops.secrets."restic/password".path;
                env = {
                  AWS_ACCESS_KEY_ID = config.sops.placeholder."restic/access_key";
                  AWS_SECRET_ACCESS_KEY = config.sops.placeholder."restic/secret_key";
                };
                status-file = "/var/lib/resticprofile/status.json";
                force-inactive-lock = true;
                initialize = true;
                cache-dir = "/var/cache/restic";
                cleanup-cache = true;
                pack-size = 64;
                backup = {
                  tag = "automatic";
                  source = cfg.settings.zpool.datasets;
                  source-base = cfg.settings.zpool.directory;
                  source-relative = true;
                  extended-status = true;
                };
                retention = {
                  after-backup = true;
                  tag = true;
                  prune = true;
                  keep-daily = cfg.restic.retention.days;
                  keep-weekly = cfg.restic.retention.weeks;
                };
              };
            };
          in
          builtins.toJSON settings;
      };
    };
  };
}
