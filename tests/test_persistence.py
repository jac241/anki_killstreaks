from datetime import datetime, timedelta
from pathlib import Path
import sqlite3

import pytest
from anki_killstreaks.persistence import DbSettings, migrate_database, AchievementsRepository
from anki_killstreaks.streaks import MultikillMedalState, NewAchievement


def test_migrate_database_creates_a_medals_database(db_settings):
    returned_settings = migrate_database(settings=db_settings)

    assert returned_settings.db_path.exists()


@pytest.fixture
def achievements_repo(db_connection):
    return AchievementsRepository(db_connection=db_connection)

@pytest.fixture
def a_new_achievement():
    return NewAchievement(
        medal=MultikillMedalState(
            name='Double Kill',
            medal_image=None,
            rank=2
        ),
        deck_id=0
    )


def test_AchievementsRepository_create_all_should_save_achievements(achievements_repo, a_new_achievement):
    achievements_repo.create_all([a_new_achievement])

    achievements = achievements_repo.all()

    assert len(achievements) == 1
    assert achievements[0].medal_name == a_new_achievement.medal_name


def test_AchievementsRepository_count_by_medal_id_returns_dict_of_counted_achievements(achievements_repo, a_new_achievement):
    medal_id = "Double Kill"
    achievements_repo.create_all([a_new_achievement, a_new_achievement, a_new_achievement])

    result = achievements_repo.count_by_medal_id()

    assert result[medal_id] == 3


def test_AchievementsRepository_todays_achievements_returns_achievements_grouped_by_medal_id_created_after_today(achievements_repo, a_new_achievement):
    achievements_repo.create_all([a_new_achievement])

    achievements_repo.conn.execute(
        "INSERT INTO achievements(medal_id, created_at, deck_id) VALUES (?, ?, ?)",
        ("Double Kill", datetime.now() - timedelta(days=2), 0)
    )

    day_start_time = datetime.combine(datetime.today().date(), datetime.min.time())
    result = achievements_repo.todays_achievements(day_start_time.timestamp())

    assert result['Double Kill'] == 1


def test_AchievementsRepository_todays_achievements_returns_achievements_for_today_scoped_by_deck_ids(achievements_repo, a_new_achievement):
    achievements_repo.create_all([a_new_achievement, a_new_achievement])

    achievements_repo.conn.execute(
        "INSERT INTO achievements(medal_id, created_at, deck_id) VALUES (?, ?, ?)",
        ("Double Kill", datetime.now() - timedelta(days=2), 0)
    )

    achievements_repo.conn.execute(
        "INSERT INTO achievements(medal_id, created_at, deck_id) VALUES (?, ?, ?)",
        ("Double Kill", datetime.now() - timedelta(days=2), 1)
    )

    day_start_time = datetime.combine(datetime.today().date(), datetime.min.time())
    result = achievements_repo.todays_achievements_for_deck_ids(
        day_start_time=day_start_time.timestamp(),
        deck_ids=[0]
    )

    assert result['Double Kill'] == 2

def test_AchievementsRepository_achievements_for_deck_ids_since_returns_correct_achievements(achievements_repo, a_new_achievement):
    achievements_repo.create_all([a_new_achievement, a_new_achievement])

    achievements_repo.conn.execute(
        "INSERT INTO achievements(medal_id, created_at, deck_id) VALUES (?, ?, ?)",
        ("Double Kill", datetime.now() - timedelta(days=31), 0)
    )

    achievements_repo.conn.execute(
        "INSERT INTO achievements(medal_id, created_at, deck_id) VALUES (?, ?, ?)",
        ("Double Kill", datetime.now() - timedelta(days=31), 1)
    )

    achievements_repo.conn.execute(
        "INSERT INTO achievements(medal_id, created_at, deck_id) VALUES (?, ?, ?)",
        ("Double Kill", datetime.now(), 1)
    )

    result = achievements_repo.achievements_for_deck_ids_since(
        deck_ids=[0],
        since_datetime=datetime.now() - timedelta(days=30)
    )

    assert result['Double Kill'] == 2


def test_AchievementsRepository_achievements_for_whole_collection_since_returns_correct_achievements(achievements_repo, a_new_achievement):
    achievements_repo.create_all([a_new_achievement, a_new_achievement])
    achievements_repo.conn.execute(
        "INSERT INTO achievements(medal_id, created_at, deck_id) VALUES (?, ?, ?)",
        ("Double Kill", datetime.now(), 1)
    )

    achievements_repo.conn.execute(
        "INSERT INTO achievements(medal_id, created_at, deck_id) VALUES (?, ?, ?)",
        ("Double Kill", datetime.now() - timedelta(days=31), 0)
    )
    achievements_repo.conn.execute(
        "INSERT INTO achievements(medal_id, created_at, deck_id) VALUES (?, ?, ?)",
        ("Double Kill", datetime.now() - timedelta(days=31), 1)
    )

    result = achievements_repo.achievements_for_whole_collection_since(
        since_datetime=datetime.now() - timedelta(days=30)
    )

    assert result['Double Kill'] == 3
