from pathlib import Path
import pytest
from anki_killstreaks.persistence import DbSettings, migrate_database


@pytest.yield_fixture()
def test_support_dir():
    test_support_dir = Path('tests', 'support').absolute()
    test_support_dir.mkdir(exist_ok=True)

    yield test_support_dir


@pytest.yield_fixture()
def db_settings(test_support_dir):
    settings = DbSettings(
        db_path=test_support_dir / 'medals.db',
        migration_dir_path=Path('anki_killstreaks', 'migrations').absolute()
    )
    yield settings

    settings.db_path.unlink()


def test_migrate_database_creates_a_medals_database(db_settings):
    migrate_database(settings=db_settings)

    assert db_settings.db_path.exists()
