"""
Anki Killstreaks add-on

Copyright: (c) jac241 2019-2020 <https://github.com/jac241>
License: GNU AGPLv3 or later <https://www.gnu.org/licenses/agpl.html>
"""
import os
from pathlib import Path
import sqlite3

os.environ['IN_TEST_SUITE'] = 'true'
os.environ['KILLSTREAKS_ENV'] = 'test'

import pytest

from anki_killstreaks.persistence import DbSettings, migrate_database, AchievementsRepository


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

    try:
        settings.db_path.unlink()
    except FileNotFoundError:
        pass


@pytest.fixture
def db_connection(db_settings):
    migrate_database(settings=db_settings)

    return sqlite3.connect(str(db_settings.db_path), isolation_level=None)


@pytest.fixture
def get_db_connection(db_settings):
    migrate_database(settings=db_settings)

    return lambda: sqlite3.connect(str(db_settings.db_path), isolation_level=None)


@pytest.fixture
def achievements_repo(get_db_connection):
    # return AchievementsRepository(db_connection=db_connection)
    return AchievementsRepository(get_db_connection)

