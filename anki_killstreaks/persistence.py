from pathlib import Path

from anki_killstreaks._vendor.yoyo import read_migrations
from anki_killstreaks._vendor.yoyo import get_backend
from anki_killstreaks._vendor import attr


@attr.s(frozen=True)
class DbSettings:
    db_path = attr.ib()
    migration_dir_path = attr.ib()

    @classmethod
    def from_addon_path(cls, addon_path):
        return cls(
            db_path=addon_path / 'user_files' / 'medals.db',
            migration_dir_path=addon_path / 'migrations'
        )

    @property
    def db_uri(self):
        return f"sqlite:///{self.db_path}"


this_addon_path = Path(__file__).parent.absolute()
default_settings = DbSettings.from_addon_path(this_addon_path)


def migrate_database(settings=default_settings):
    backend = get_backend(settings.db_uri)
    migrations = read_migrations(str(settings.migration_dir_path))

    with backend.lock():
        backend.apply_migrations(backend.to_apply(migrations))
