from datetime import datetime, timedelta
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


def test_AcheivementsRepository_count_by_medal_id_returns_dict_of_counted_acheivements(acheivements_repo, a_new_acheivement):
    medal_id = "Double Kill"
    acheivements_repo.create_all([a_new_acheivement, a_new_acheivement, a_new_acheivement])

    result = acheivements_repo.count_by_medal_id()

    assert result[medal_id] == 3


def test_AcheivementsRepository_todays_acheivements_returns_acheivements_grouped_by_medal_id_created_after_today(acheivements_repo, a_new_acheivement):
    acheivements_repo.create_all([a_new_acheivement])

    acheivements_repo.conn.execute(
        "INSERT INTO acheivements(medal_id, created_at) VALUES (?, ?)",
        ("Double Kill", datetime.now() - timedelta(days=2))
    )

    day_start_time = datetime.combine(datetime.today().date(), datetime.min.time()) + timedelta(hours=4)
    result = acheivements_repo.todays_acheivements(day_start_time.timestamp())

    assert result['Double Kill'] == 1

