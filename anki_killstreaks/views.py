from collections import Counter

import attr
import base64


def MedalsOverviewJS(acheivements):
    return AppendingInjector(html=MedalsOverview(medal_types(acheivements)))


def AppendingInjector(html):
    return f"$('body').append(String.raw`{html}`);".replace("\n", " ")


def medal_types(acheivements):
    counter = Counter(a.medal_name for a in acheivements)

    unique_achievements = list(dict.fromkeys(acheivements))
    acheivements_by_name = dict(
        (a.medal_name, a)
        for a
        in unique_achievements
    )

    return [
        MedalType(
            name=key,
            img_src=acheivements_by_name[key].medal_img_src,
            count=value,
        )
        for key, value
        in counter.items()
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


def MedalsOverview(medal_types):
    medals = ""
    for medal_type in medal_types:
        medals += f"{Medal(medal_type)}"

    return f"""
        {Head()}
        <center>
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

