import codecs
from datetime import datetime
from functools import partial
import json
import requests
from urllib.parse import urljoin

from . import accounts
from ._vendor import attr
from .networking import shared_headers, sra_base_url
from .persistence import PersistedAchievement, min_datetime


def sync_if_logged_in(user_repo, achievements_repo, network_thread):
    if accounts.check_user_logged_in(user_repo):
        sync_job = partial(
            sync_achievements,
            user_repo,
            achievements_repo
        )
        network_thread.put(sync_job)


def sync_achievements(user_repo, achievements_repo):
    try:
        since_datetime = get_latest_sync_date(user_repo)
        achievements_attrs = load_achievements_attrs_since(achievements_repo, since_datetime)
        compressed_attrs = compress_achievements_attrs(achievements_attrs)

        response = post_compressed_achievements(user_repo, compressed_attrs)
        response.raise_for_status()
    except requests.HTTPError as e:
        print(e)


def get_latest_sync_date(user_repo, shared_headers=shared_headers):
    auth_headers = accounts.load_auth_headers(user_repo)

    headers = shared_headers.copy()
    headers.update(auth_headers)

    response = requests.get(
        url=urljoin(sra_base_url, "/api/v1/syncs"),
        headers=headers,
    )

    response.raise_for_status()

    syncs_attrs = response.json()
    if len(syncs_attrs) > 0:
        return datetime.strptime(
            syncs_attrs[-1]["created_at"],
            '%Y-%m-%dT%H:%M:%S.%fZ'
        )
    else:
        return min_datetime


def load_achievements_attrs_since(achievements_repo, since_datetime):
    return [
        attr.asdict(a, filter=attr.filters.exclude(attr.fields(PersistedAchievement).medal))
        for a in achievements_repo.all(since_datetime)
    ]


def compress_achievements_attrs(attrs):
    return codecs.encode(
        bytes(json.dumps(attrs), "utf-8"),
        "zlib",
    )


def post_compressed_achievements(user_repo, compressed_attrs):
    auth_headers = accounts.load_auth_headers(user_repo)
    response =  requests.post(
        url=urljoin(sra_base_url, "/api/v1/syncs"),
        data={
            "client_uuid": "fda4cb0d-b6e3-4e5f-b7b1-d338351ccead",
        },
        files={
            'achievements_file': (
                'achievements.json.zlib',
                compressed_attrs,
                "application/zlib",
            )
        },
        timeout=5,
        headers=auth_headers,
    )

    response.raise_for_status()

    return response
