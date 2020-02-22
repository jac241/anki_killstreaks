from pathlib import Path
import sqlite3

import pytest
from anki_killstreaks.persistence import DbSettings, migrate_database, AcheivementsRepository
from anki_killstreaks.streaks import MultikillMedalState, NewAcheivement


def test_migrate_database_creates_a_medals_database(db_settings):
    returned_settings = migrate_database(settings=db_settings)

    assert returned_settings.db_path.exists()


@pytest.fixture
def acheivements_repo(db_connection):
    return AcheivementsRepository(db_connection=db_connection)

@pytest.fixture
def a_new_acheivement():
    return NewAcheivement(
        medal=MultikillMedalState(
            name='Double Kill',
            medal_image=None
        )
    )


def test_AcheivementsRepository_create_all_should_save_acheivements(acheivements_repo, a_new_acheivement):
    acheivements_repo.create_all([a_new_acheivement])

    acheivements = acheivements_repo.all()

    assert len(acheivements) == 1
    assert acheivements[0].medal_name == a_new_acheivement.medal_name


def test_AcheivementsRepository_count_by_medal_id_returns_array_of_counted_acheivements(acheivements_repo, a_new_acheivement):
    acheivements_repo.create_all([a_new_acheivement])
