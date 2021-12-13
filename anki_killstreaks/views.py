from collections import Counter
from pathlib import Path

import attr
import base64

from ._vendor.jinja2 import Template
from .toolz import unique, join, groupby
from .streaks import get_all_displayable_medals, all_game_ids


def MedalsOverviewHTML(achievements, header_text, current_game_id):
    return (
        MedalsOverview(
            medal_types=medal_types(achievements),
            header_text=header_text,
            current_game_id=current_game_id,
        )
        + MedalsOverviewScript()
    )


def MedalsOverviewScript():
    return f"<script>{js_content('medals_overview.js')}</script>"


def TodaysMedalsJS(achievements, current_game_id):
    return AppendingInjector(
        html=MedalsOverview(
            medal_types=medal_types(achievements),
            header_text="All medals earned today:",
            current_game_id=current_game_id,
        )
    )


def TodaysMedalsForDeckJS(achievements, deck, current_game_id):
    return AppendingInjector(
        html=MedalsOverview(
            medal_types=medal_types(achievements),
            header_text=f'Medals earned today reviewing deck "{deck.name}":',
            current_game_id=current_game_id,
        )
    )


def AppendingInjector(html):
    return f"$('body').append(String.raw`{html}`);".replace("\n", " ")


def medal_types_by_game_id(medal_types, game_ids):
    medal_types = groupby(lambda mt: mt.game_id, medal_types)

    for game_id in game_ids:
        if not game_id in medal_types:
            medal_types[game_id] = []

    return medal_types


def medal_types(achievement_count_by_medal_id: dict):
    medal_count_pairs = join(
        leftseq=get_all_displayable_medals(),
        rightseq=achievement_count_by_medal_id.items(),
        leftkey=lambda dm: dm.id_,
        rightkey=lambda ac: ac[0],
    )

    sorted_medals_with_counts = sorted(
        medal_count_pairs,
        key=lambda medal_count_pairs: medal_count_pairs[0].rank,
    )

    return [
        MedalType(
            medal=medal,
            name=medal.name,
            img_src=medal.medal_image,
            count=count,
        )
        for medal, (medal_id, count) in sorted_medals_with_counts
    ]


@attr.s(frozen=True)
class MedalType:
    medal = attr.ib()
    name = attr.ib()
    img_src = attr.ib()
    count = attr.ib()

    @property
    def img_base64(self):
        with open(self.img_src, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode("utf-8")

        return f"data:image/png;base64,{encoded_string}"

    @property
    def game_id(self):
        return self.medal.game_id


_templates_dir = Path(__file__).parent / "templates"


def MedalsOverview(
    medal_types,
    current_game_id,
    header_text="Medals earned this session:",
):
    with open(_templates_dir / "medals_overview.html", "r") as f:
        template = Template(f.read())

    return template.render(
        medal_types_by_game_id=medal_types_by_game_id(
            medal_types, all_game_ids
        ),
        header_text=header_text,
        game_names_by_id=dict(
            halo_3="Halo 3",
            mw2="Call of Duty: Modern Warfare 2",
            halo_5="Halo 5",
            halo_infinite="Halo Infinite",
        ),
        selected_game_id=current_game_id,
    )


def js_content(filename):
    js_file = Path(__file__).parent / "js" / filename
    with open(js_file, "r") as f:
        js = f.read()
    return js.replace("\n", "")


def html_content(filename):
    html_file = Path(__file__).parent / "web" / filename
    with open(html_file, "r") as f:
        return f.read()
