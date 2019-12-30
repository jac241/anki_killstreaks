from anki_killstreaks.views import render_medals_overview, medal_types
from anki_killstreaks.streaks import Acheivement, KillingSpreeMedalState, \
    image_path

def test_render_medals_overview_should_append_medals_view_to_old_result():
    result = render_medals_overview(
        self=None,
        _old=lambda _: "result",
        acheivements=[
            Acheivement(
                medal=KillingSpreeMedalState(
                    name='Double kill',
                    medal_image=image_path('Doublekill_Medal.webp.png')
                )
            ),
        ]
    )

    assert len(result) > len("result")


def test_medal_types_should_group_acheivements_and_count_medals():
    acheivements = [
        Acheivement(
            medal=KillingSpreeMedalState(
                name='Double kill',
                medal_image=image_path('Doublekill_Medal.webp.png')
            )
        ),
        Acheivement(
            medal=KillingSpreeMedalState(
                name='Double kill',
                medal_image=image_path('Doublekill_Medal.webp.png')
            )
        ),
        Acheivement(
            medal=KillingSpreeMedalState(
                name='Triple kill',
                medal_image=image_path('Doublekill_Medal.webp.png')
            )
        ),
    ]

    results = medal_types(acheivements=acheivements)

    assert len(results) == 2
    assert results[0].name == 'Double kill'
    assert results[0].count == 2
    assert results[1].name == 'Triple kill'
    assert results[1].count == 1
