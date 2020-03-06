from collections import Counter

import attr
import base64

from anki_killstreaks.toolz import unique, join
from anki_killstreaks.streaks import get_all_displayable_medals


def MedalsOverviewHTML(achievements, header_text):
    return MedalsOverview(medal_types(achievements), header_text)


def TodaysMedalsJS(achievements):
    return AppendingInjector(
        html=MedalsOverview(
            medal_types=medal_types(achievements),
            header_text="All medals earned today:"
        )
    )


def TodaysMedalsForDeckJS(achievements, deck):
    return AppendingInjector(
        html=MedalsOverview(
            medal_types=medal_types(achievements),
            header_text=f'Medals earned today reviewing deck "{deck.name}":'
        )
    )


def AppendingInjector(html):
    return f"$('body').append(String.raw`{html}`);".replace("\n", " ")


def medal_types(achievement_count_by_medal_id: dict):
    medal_count_pairs = join(
        leftseq=get_all_displayable_medals(),
        rightseq=achievement_count_by_medal_id.items(),
        leftkey=lambda dm: dm.id_,
        rightkey=lambda ac: ac[0]
    )

    sorted_medals_with_counts = sorted(
        medal_count_pairs,
        key=lambda medal_count_pairs: medal_count_pairs[0].rank
    )

    return [
        MedalType(
            name=medal.name,
            img_src=medal.medal_image,
            count=count,
        )
        for medal, (medal_id, count)
        in sorted_medals_with_counts
    ]


@attr.s(frozen=True)
class MedalType:
    name = attr.ib()
    img_src = attr.ib()
    count = attr.ib()

    @property
    def img_base64(self):
        with open(self.img_src, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode("utf-8")

        return f"data:image/png;base64,{encoded_string}"


def Head():
    return """
        <style>
            .medals-overview {
                display: flex;
                flex-wrap: wrap;
                max-width: 750px;
                margin-top: 2em;
                justify-content: center;
                text-align: center;
            }
            .medal-type {
                width: 7.4em;
                margin-bottom: 0.75em;
            }
            .medal-type h4 {
                margin-top: 0.25em;
                margin-bottom: 0.25em;
            }
            .medal-type p {
                margin-top: 0.25em;
                margin-bottom: 0.25em;
            }
        </style>
    """


def MedalsOverview(medal_types, header_text="Medals earned this session:"):
    medals = ""
    for medal_type in medal_types:
        medals += f"{Medal(medal_type)}"

    medal_header = (
        rf"<h3>{header_text}</h3>"
        if len(medals) > 0
        else ""
    )

    return f"""
        {Head()}
        <center>
            {medal_header}
            <div class="medals-overview">
                {medals}
            </div>
        </center>
    """

def Medal(medal_type):
    return f"""
        <div class="medal-type">
            <img src="{medal_type.img_base64}">
            <h4>{medal_type.name}</h4>
            <p>{medal_type.count}</p>
        </div>
    """

