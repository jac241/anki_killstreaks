from datetime import datetime, timedelta, date, timezone, time
import itertools
from pathlib import Path
import sqlite3

from anki_killstreaks._vendor import attr
from anki_killstreaks._vendor.yoyo import read_migrations
from anki_killstreaks._vendor.yoyo import get_backend

from anki_killstreaks.toolz import join
from anki_killstreaks.streaks import get_all_displayable_medals


this_addon_path = Path(__file__).parent.absolute()
min_datetime = datetime(year=2019, month=12, day=25) # day I started making the addon :-)


@attr.s(frozen=True)
class DbSettings:
    db_path = attr.ib()
    migration_dir_path = attr.ib()

    @classmethod
    def from_profile_folder_path(
        cls,
        profile_folder_path,
        addon_path=this_addon_path
    ):
        return cls(
            db_path=profile_folder_path / 'anki_killstreaks.db',
            migration_dir_path=addon_path / 'migrations'
        )

    @property
    def db_uri(self):
        return f"sqlite:///{self.db_path}"


this_addon_path = Path(__file__).parent.absolute()
# default_settings = DbSettings.from_addon_path(this_addon_path)


def migrate_database(settings):
    backend = get_backend(settings.db_uri)
    migrations = read_migrations(str(settings.migration_dir_path))

    with backend.lock():
        backend.apply_migrations(backend.to_apply(migrations))

    return settings


def get_db_connection(db_settings):
    return sqlite3.connect(str(db_settings.db_path), isolation_level=None)


class AchievementsRepository:
    def __init__(self, db_connection):
        self.conn = db_connection

    def create_all(self, new_achievements):
        self.conn.executemany(
            "INSERT INTO achievements(medal_id, deck_id) VALUES (?, ?)",
            ((a.medal_id, a.deck_id) for a in new_achievements)
        )

    # only used by tests, should eliminate
    def all(self):
        cursor = self.conn.execute("SELECT * FROM achievements")

        loaded_achievements = [
            PersistedAchievement(*row, medal=None)
            for row
            in cursor
        ]

        # will probably become a performance issue, move to
        # spot where we need this join.
        matches = join(
            leftseq=get_all_displayable_medals(),
            rightseq=loaded_achievements,
            leftkey=lambda dm: dm.id_,
            rightkey=lambda la: la.medal_id
        )

        return [
            persisted_achievement.with_medal(medal)
            for medal, persisted_achievement
            in matches
        ]


    def todays_achievements(self, day_start_time):
        return self.count_by_medal_id(created_at_gt=day_start_time)

    def count_by_medal_id(self, created_at_gt=min_datetime):
        cursor = self.conn.execute(
            """
            SELECT medal_id, count(*)
            FROM achievements
            WHERE created_at > ?
            GROUP BY medal_id
            """,
            (created_at_gt.astimezone(timezone.utc),)
        )

        return dict(row for row in cursor)

    def todays_achievements_for_deck_ids(self, day_start_time, deck_ids):
        return self.achievements_for_deck_ids_since(
            deck_ids=deck_ids,
            since_datetime=day_start_time
        )

    def achievements_for_deck_ids_since(self, deck_ids, since_datetime):
        cursor = self.conn.execute(
            f"""
            SELECT medal_id, count(*)
            FROM achievements
            WHERE created_at > ? AND
                deck_id in ({','.join('?' for i in deck_ids)})
            GROUP BY medal_id
            """,
            (since_datetime.astimezone(timezone.utc), *deck_ids)
        )

        return dict(row for row in cursor)

    def achievements_for_whole_collection_since(self, since_datetime):
        cursor = self.conn.execute(
            f"""
            SELECT medal_id, count(*)
            FROM achievements
            WHERE created_at > ?
            GROUP BY medal_id
            """,
            (since_datetime.astimezone(timezone.utc),)
        )

        return dict(row for row in cursor)


@attr.s
class PersistedAchievement:
    id_ = attr.ib()
    medal_id = attr.ib()
    created_at = attr.ib()
    deck_id = attr.ib()
    medal = attr.ib()

    def with_medal(self, medal):
        return attr.evolve(self, medal=medal)

    @property
    def medal_name(self):
        return self.medal.name

    @property
    def medal_img_src(self):
        return self.medal.medal_image


def day_start_time(rollover_hour, current_time=datetime.now()):
    if current_time.hour > rollover_hour:
        return datetime.combine(current_time.date(), time(hour=rollover_hour))
    else:
        yesterday = current_time - timedelta(days=1)
        return datetime.combine(yesterday.date(), time(hour=rollover_hour))


class SettingsRepository:
    def __init__(self, db_connection):
        self.conn = db_connection

    @property
    def current_game_id(self):
        cursor = self.conn.execute("SELECT current_game_id FROM settings;")
        return cursor.fetchone()[0]

    @current_game_id.setter
    def current_game_id(self, game_id):
        self.conn.execute(
            "UPDATE settings SET current_game_id = ?",
            (game_id,)
        )

    def toggle_auto_switch_game(self):
        return True
