from datetime import datetime, timedelta, date, timezone
from pathlib import Path
import sqlite3

import pytest
from anki_killstreaks.persistence import (
    DbSettings,
    migrate_database,
    AchievementsRepository,
    day_start_time,
    SettingsRepository,
)
from anki_killstreaks.streaks import (
    MultikillMedalState,
    NewAchievement,
    DEFAULT_GAME_ID,
)


def test_migrate_database_creates_a_medals_database(db_settings):
    returned_settings = migrate_database(settings=db_settings)

    assert returned_settings.db_path.exists()


@pytest.fixture
def a_new_achievement():
    return NewAchievement(
        medal=MultikillMedalState(
            id_='Double Kill',
            name='Double Kill',
            medal_image=None,
            rank=2,
            game_id='halo_3'
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

    with achievements_repo.get_db_connection() as conn:
        conn.execute(
            "INSERT INTO achievements(medal_id, created_at, deck_id) VALUES (?, ?, ?)",
            ("Double Kill", datetime.now().astimezone(timezone.utc) - timedelta(days=2), 0)
        )

    # I guess don't run this at 4am lol
    result = achievements_repo.todays_achievements(day_start_time(rollover_hour=4))

    assert result['Double Kill'] == 1


def test_AchievementsRepository_todays_achievements_returns_achievements_for_today_scoped_by_deck_ids(achievements_repo, a_new_achievement):
    achievements_repo.create_all([a_new_achievement, a_new_achievement])

    with achievements_repo.get_db_connection() as conn:
        conn.execute(
            "INSERT INTO achievements(medal_id, created_at, deck_id) VALUES (?, ?, ?)",
            ("Double Kill", datetime.now() - timedelta(days=2), 0)
        )

        conn.execute(
            "INSERT INTO achievements(medal_id, created_at, deck_id) VALUES (?, ?, ?)",
            ("Double Kill", datetime.now() - timedelta(days=2), 1)
        )

    day_start_time = datetime.combine(datetime.today().date(), datetime.min.time())
    result = achievements_repo.todays_achievements_for_deck_ids(
        day_start_time=day_start_time,
        deck_ids=[0]
    )

    assert result['Double Kill'] == 2

def test_AchievementsRepository_achievements_for_deck_ids_since_returns_correct_achievements(achievements_repo, a_new_achievement):
    achievements_repo.create_all([a_new_achievement, a_new_achievement])

    with achievements_repo.get_db_connection() as conn:
        conn.execute(
            "INSERT INTO achievements(medal_id, created_at, deck_id) VALUES (?, ?, ?)",
            ("Double Kill", datetime.now() - timedelta(days=31), 0)
        )

        conn.execute(
            "INSERT INTO achievements(medal_id, created_at, deck_id) VALUES (?, ?, ?)",
            ("Double Kill", datetime.now() - timedelta(days=31), 1)
        )

        conn.execute(
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

    with achievements_repo.get_db_connection() as conn:
        conn.execute(
            "INSERT INTO achievements(medal_id, created_at, deck_id) VALUES (?, ?, ?)",
            ("Double Kill", datetime.now(), 1)
        )
        conn.execute(
            "INSERT INTO achievements(medal_id, created_at, deck_id) VALUES (?, ?, ?)",
            ("Double Kill", datetime.now() - timedelta(days=31), 0)
        )
        conn.execute(
            "INSERT INTO achievements(medal_id, created_at, deck_id) VALUES (?, ?, ?)",
            ("Double Kill", datetime.now() - timedelta(days=31), 1)
        )

    result = achievements_repo.achievements_for_whole_collection_since(
        since_datetime=datetime.now() - timedelta(days=30)
    )

    assert result['Double Kill'] == 3


def test_day_start_time_should_return_4am_today_if_it_is_after_4am():
    result = day_start_time(rollover_hour=4)

    today = datetime.today()
    assert result == datetime(
        year=today.year, month=today.month, day=today.day, hour=4
    )


def test_day_start_time_should_return_4_am_yesterday_if_it_is_before_4am_today():
    midnight_today = datetime.combine(datetime.now().date(), datetime.min.time())
    result = day_start_time(rollover_hour=4, current_time=midnight_today)

    yesterday = datetime.today() - timedelta(days=1)
    assert result == datetime(
        year=yesterday.year, month=yesterday.month, day=yesterday.day, hour=4
    )


@pytest.fixture
def settings_repo(get_db_connection):
    return SettingsRepository(get_db_connection=get_db_connection)


def test_SettingsRepository_current_game_id_should_return_default_game_id_on_first_run(settings_repo):
    assert settings_repo.current_game_id == DEFAULT_GAME_ID


def test_SettingsRepository_current_game_id_should_be_able_to_be_saved(settings_repo):
    settings_repo.current_game_id = "new_game"
    assert settings_repo.current_game_id == "new_game"


def test_SettingsRepository_toggle_auto_switch_game_should_do_what_it_says(settings_repo):
    with settings_repo.get_db_connection() as conn:
        conn.execute("UPDATE settings SET should_auto_switch_game = ?", (True,))
    settings_repo.toggle_auto_switch_game()
    assert settings_repo.should_auto_switch_game == False


def test_SettingsRepository_auto_switch_game_status_should_return_stored_status(settings_repo):
    with settings_repo.get_db_connection() as conn:
        conn.execute("UPDATE settings SET should_auto_switch_game = ?", (True,))
    assert settings_repo.should_auto_switch_game == True


def test_SettingsRepository_should_auto_switch_games_defaults_to_false(settings_repo):
    assert settings_repo.should_auto_switch_game == False


def test_SettingsRepository_toggle_chase_mode_should_toggle_chase_mode(settings_repo):
    with settings_repo.get_db_connection() as conn:
        conn.execute("UPDATE settings SET should_show_chase_mode = ?", (True,))
    settings_repo.toggle_chase_mode()
    assert settings_repo.should_show_chase_mode is False

