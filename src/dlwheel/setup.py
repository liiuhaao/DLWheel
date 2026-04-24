from . import BackupSystem, ConfigLoader


def _backup_enabled(cfg):
    """Return True if backup is enabled, handling both bool and dict forms."""
    if cfg.backup is True:
        return True
    if isinstance(cfg.backup, dict) and cfg.backup:
        return True
    return False


def setup():
    try:
        cfg = ConfigLoader().run()
    except Exception as e:
        print(f"[dlwheel] Config load failed: {e}")
        raise

    if _backup_enabled(cfg):
        try:
            BackupSystem(cfg).run()
        except Exception as e:
            print(f"[dlwheel] Backup failed (training continues): {e}")

    return cfg
