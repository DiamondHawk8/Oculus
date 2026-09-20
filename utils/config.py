from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config.toml"


@dataclass(frozen=True)
class AppConfig:
    database_path: Path
    log_path: Path
    backup_dir: Path
    operation_backup_dir: Path
    collection_root: Path | None
    backup_on_startup: bool
    migrate_drive_comments: bool
    migration_root: Path | None


def _path(value: str | None, *, base_dir: Path) -> Path | None:
    if not value:
        return None
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = base_dir / path
    return path.resolve(strict=False)


def _required_path(value: str, *, base_dir: Path) -> Path:
    path = _path(value, base_dir=base_dir)
    if path is None:
        raise ValueError("A required configured path cannot be empty")
    return path


def load_config(config_path: str | Path = DEFAULT_CONFIG_PATH) -> AppConfig:
    """Load optional TOML settings while retaining portable, local defaults."""
    config_path = Path(config_path).expanduser().resolve(strict=False)
    data = {}
    if config_path.is_file():
        with config_path.open("rb") as config_file:
            data = tomllib.load(config_file)

    paths = data.get("paths", {})
    maintenance = data.get("maintenance", {})
    base_dir = config_path.parent

    return AppConfig(
        database_path=_required_path(paths.get("database", "oculus.db"), base_dir=base_dir),
        log_path=_required_path(paths.get("log", "logs/oculus.log"), base_dir=base_dir),
        backup_dir=_required_path(paths.get("backup_dir", "backups"), base_dir=base_dir),
        operation_backup_dir=_required_path(
            paths.get("operation_backup_dir", "~/OculusBackups"),
            base_dir=base_dir,
        ),
        collection_root=_path(paths.get("collection_root"), base_dir=base_dir),
        backup_on_startup=bool(maintenance.get("backup_on_startup", True)),
        migrate_drive_comments=bool(maintenance.get("migrate_drive_comments", False)),
        migration_root=_path(
            maintenance.get("migration_root") or paths.get("collection_root"),
            base_dir=base_dir,
        ),
    )
