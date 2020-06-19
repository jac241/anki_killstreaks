import sqlite3
from datetime import datetime, timedelta, timezone, time
from pathlib import Path

from ._vendor import attr
from ._vendor.yoyo import get_backend
from ._vendor.yoyo import read_migrations
from .streaks import get_all_displayable_medals
from .toolz import join

this_addon_path = Path(__file__).parent.absolute()
min_datetime = datetime(
    year=2019, month=12, day=25
)  # day I started making the addon :-)


@attr.s(frozen=True)
class DbSettings:
    db_path = attr.ib()
    migration_dir_path = attr.ib()

    @classmethod
    def from_profile_folder_path(
        cls, profile_folder_path, addon_path=this_addon_path
    ):
        return cls(
            db_path=profile_folder_path / "anki_killstreaks.db",
            migration_dir_path=addon_path / "migrations",
        )

    @property
    def db_uri(self):
        return f"sqlite:///{self.db_path}"


def migrate_database(settings):
    backend = get_backend(settings.db_uri)
    migrations = read_migrations(str(settings.migration_dir_path))

    with backend.lock():
        backend.apply_migrations(backend.to_apply(migrations))

    return settings


def get_db_connection(db_settings):
    return sqlite3.connect(str(db_settings.db_path), isolation_level=None)


class AchievementsRepository:
    def __init__(self, get_db_connection):
        self.get_db_connection = get_db_connection

    def create_all(self, new_achievements):
        with self.get_db_connection() as conn:
            row_ids = []

            for new_a in new_achievements:
                cursor = conn.execute(
                    "INSERT INTO achievements(medal_id, deck_id) VALUES (?, ?)",
                    (new_a.medal_id, new_a.deck_id),
                )
                row_ids.append(cursor.lastrowid)

            in_placeholders = ",".join(["?"] * len(row_ids))
            select_cursor = conn.execute(
                f"""
                SELECT *
                FROM achievements
                WHERE id in ({in_placeholders})
                """,
                tuple(row_ids)
            )

            return [PersistedAchievement(*row, medal=None) for row in select_cursor]

    # only used by tests, should eliminate
    def all(self, since_datetime=min_datetime):
        with self.get_db_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM achievements
                WHERE created_at > ?
                """,
                (since_datetime, )
            )

            loaded_achievements = [
                PersistedAchievement(*row, medal=None) for row in cursor
            ]

        # will probably become a performance issue, move to
        # spot where we need this join.
        matches = join(
            leftseq=get_all_displayable_medals(),
            rightseq=loaded_achievements,
            leftkey=lambda dm: dm.id_,
            rightkey=lambda la: la.medal_id,
        )

        return [
            persisted_achievement.with_medal(medal)
            for medal, persisted_achievement in matches
        ]

    def todays_achievements(self, day_start_time):
        return self.count_by_medal_id(created_at_gt=day_start_time)

    def count_by_medal_id(self, created_at_gt=min_datetime):
        with self.get_db_connection() as conn:
            cursor = conn.execute(
                """
                SELECT medal_id, count(*)
                FROM achievements
                WHERE created_at > ?
                GROUP BY medal_id
                """,
                (created_at_gt.astimezone(timezone.utc),),
            )

            return dict(row for row in cursor)

    def todays_achievements_for_deck_ids(self, day_start_time, deck_ids):
        return self.achievements_for_deck_ids_since(
            deck_ids=deck_ids, since_datetime=day_start_time
        )

    def achievements_for_deck_ids_since(self, deck_ids, since_datetime):
        with self.get_db_connection() as conn:
            cursor = conn.execute(
                f"""
                SELECT medal_id, count(*)
                FROM achievements
                WHERE created_at > ? AND
                    deck_id in ({','.join('?' for i in deck_ids)})
                GROUP BY medal_id
                """,
                (since_datetime.astimezone(timezone.utc), *deck_ids),
            )

            return dict(row for row in cursor)

    def achievements_for_whole_collection_since(self, since_datetime):
        with self.get_db_connection() as conn:
            cursor = conn.execute(
                f"""
                SELECT medal_id, count(*)
                FROM achievements
                WHERE created_at > ?
                GROUP BY medal_id
                """,
                (since_datetime.astimezone(timezone.utc),),
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
    def __init__(self, get_db_connection):
        self.get_db_connection = get_db_connection

    @property
    def current_game_id(self):
        with self.get_db_connection() as conn:
            cursor = conn.execute("SELECT current_game_id FROM settings;")
            return cursor.fetchone()[0]

    @current_game_id.setter
    def current_game_id(self, game_id):
        with self.get_db_connection() as conn:
            conn.execute("UPDATE settings SET current_game_id = ?", (game_id,))

    def toggle_auto_switch_game(self):
        with self.get_db_connection() as conn:
            conn.execute(
                "UPDATE settings SET should_auto_switch_game = NOT should_auto_switch_game"
            )

    @property
    def should_auto_switch_game(self):
        with self.get_db_connection() as conn:
            cursor = conn.execute(
                "SELECT should_auto_switch_game FROM settings;"
            )
            return cursor.fetchone()[0]
