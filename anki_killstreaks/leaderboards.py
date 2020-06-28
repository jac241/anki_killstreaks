import codecs
from datetime import datetime
from functools import partial
import json
import requests
from urllib.parse import urljoin
import uuid

from . import accounts
from ._vendor import attr
from .networking import sra_base_url, RequeuingJob
from .persistence import PersistedAchievement, min_datetime


def ensure_client_uuid_exists(user_repo):
    user = user_repo.load()

    if not user.client_uuid:
        user_repo.set_client_uuid(str(uuid.uuid4()))


def sync_if_logged_in(user_repo, achievements_repo, network_thread, http_client):
    if accounts.check_user_logged_in(user_repo):
        sync_job = RequeuingJob(
            partial(
                _sync_achievements,
                user_repo,
                achievements_repo,
                http_client,
            ),
            job_queue=network_thread,
            exception_to_retry_on=requests.exceptions.ConnectionError,
        )
        network_thread.put(sync_job)


def _sync_achievements(user_repo, achievements_repo, http_client):
    try:
        since_datetime = _get_latest_sync_date(user_repo, http_client)
        achievements_attrs = _load_achievements_attrs_since(achievements_repo, since_datetime)
        compressed_attrs = _compress_achievements_attrs(achievements_attrs)

        response = _post_compressed_achievements(user_repo, http_client, compressed_attrs)
        accounts.store_auth_headers(user_repo, response.headers)

        response.raise_for_status()
    except requests.HTTPError as e:
        print(e)
        raise e


def _get_latest_sync_date(user_repo, http_client):
    response = http_client.get(url=urljoin(sra_base_url, "/api/v1/syncs"))

    response.raise_for_status()

    syncs_attrs = response.json()
    if len(syncs_attrs) > 0:
        return datetime.strptime(
            syncs_attrs[-1]["created_at"],
            '%Y-%m-%dT%H:%M:%S.%fZ'
        )
    else:
        return min_datetime


def _load_achievements_attrs_since(achievements_repo, since_datetime):
    return [
        attr.asdict(a, filter=attr.filters.exclude(attr.fields(PersistedAchievement).medal))
        for a in achievements_repo.all(since_datetime)
    ]


def _compress_achievements_attrs(attrs):
    return codecs.encode(
        bytes(json.dumps(attrs), "utf-8"),
        "zlib",
    )


def _post_compressed_achievements(user_repo, http_client, compressed_attrs):
    user = user_repo.load()

    response = http_client.post(
        url=urljoin(sra_base_url, "/api/v1/syncs"),
        data={
            "client_uuid": user.client_uuid,
        },
        files={
            'achievements_file': (
                'achievements.json.zlib',
                compressed_attrs,
                "application/zlib",
            )
        },
        timeout=5,
        skip_shared_headers=True
    )

    response.raise_for_status()

    return response


@attr.s(frozen=True)
class RemoteAchievementsRepository:
    _local_repo = attr.ib()
    _user_repo = attr.ib()
    _job_queue = attr.ib()
    _http_client = attr.ib()

    def create_all(self, *args, **kwargs):
        persisted_achievements = self._local_repo.create_all(*args, **kwargs)
        if accounts.check_user_logged_in(self._user_repo):
            for achievement in persisted_achievements:
                job = RequeuingJob(
                    partial(
                        _post_achievement,
                        user=self._user_repo.load(),
                        achievement=achievement,
                        http_client=self._http_client,
                    ),
                    job_queue=self._job_queue,
                    exception_to_retry_on=requests.exceptions.ConnectionError,
                )
                self._job_queue.put(job)

    def __getattr__(self, attr):
        return getattr(self._local_repo, attr)


def _post_achievement(user, http_client, achievement):
    response = http_client.post(
        url=urljoin(sra_base_url, "/api/v1/achievements"),
        json=dict(
            client_db_id=achievement.id_,
            client_medal_id=achievement.medal_id,
            client_deck_id=achievement.deck_id,
            client_earned_at=achievement.created_at,
            client_uuid=user.client_uuid,
        ),
    )

    response.raise_for_status()

