from anki_killstreaks.views import medal_types, AppendingInjector, \
        TodaysMedalsJS
from anki_killstreaks.streaks import NewAcheivement, KillingSpreeMedalState, \
        image_path


def test_medal_types_should_group_acheivements_and_count_medals():
    acheivement_count_by_medal_id = {
        'Double Kill': 2,
        'Triple Kill': 1
    }

    results = medal_types(acheivement_count_by_medal_id)

    assert len(results) == 2
    assert results[0].name == 'Double Kill'
    assert results[0].count == 2
    assert results[1].name == 'Triple Kill'
    assert results[1].count == 1


def test_MedalsOverviewJS_smoke_test():
    assert TodaysMedalsJS(
        {
            'Double Kill': 2
        }
    )
