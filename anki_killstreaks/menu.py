from functools import partial
from aqt.qt import QMenu

from anki_killstreaks.game import (
    load_current_game_id,
    set_current_game_id,
    toggle_auto_switch_game,
)


def connect_menu(main_window, profile_controller):
    # probably overdoing it with partial functions here... but none of these
    # need to be classes honestly
    top_menu = QMenu('Killstreaks', main_window)
    game_menu = QMenu('Select Game', main_window)

    halo_3_action = game_menu.addAction('Halo 3')
    halo_3_action.setCheckable(True)
    halo_3_action.triggered.connect(
        partial(
            set_current_game_id,
            game_id='halo_3',
            get_settings_repo=profile_controller.get_settings_repo,
            on_game_changed=profile_controller.change_game,
        )
    )

    mw2_action = game_menu.addAction('Call of Duty: Modern Warfare 2')
    mw2_action.setCheckable(True)
    mw2_action.triggered.connect(
        partial(
            set_current_game_id,
            game_id='mw2',
            get_settings_repo=profile_controller.get_settings_repo,
            on_game_changed=profile_controller.change_game,
        )
    )

    halo_5_action = game_menu.addAction('Halo 5')
    halo_5_action.setCheckable(True)
    halo_5_action.triggered.connect(
        partial(
            set_current_game_id,
            game_id='halo_5',
            get_settings_repo=profile_controller.get_settings_repo,
            on_game_changed=profile_controller.change_game,
        )
    )

    top_menu.addMenu(game_menu)

    game_menu.aboutToShow.connect(
        partial(
            check_correct_game_in_menu,
            menu_actions_by_game_id=dict(
                halo_3=halo_3_action,
                mw2=mw2_action,
                halo_5=halo_5_action,
            ),
            load_current_game_id=partial(
                load_current_game_id,
                get_settings_repo=profile_controller.get_settings_repo
            ),
        )
    )

    auto_switch_game_action = top_menu.addAction('Automatically Switch Games')
    auto_switch_game_action.setCheckable(True)
    auto_switch_game_action.triggered.connect(
        partial(
            toggle_auto_switch_game,
            get_settings_repo=profile_controller.get_settings_repo,
            on_auto_switch_game_toggled=profile_controller.toggle_auto_switch_game,
        )
    )

    top_menu.aboutToShow.connect(
        partial(
            set_check_for_auto_switch_game,
            action=auto_switch_game_action,
            load_auto_switch_game_status=lambda: None
        )
    )

    main_window.form.menubar.addMenu(top_menu)


def check_correct_game_in_menu(menu_actions_by_game_id, load_current_game_id):
    current_game_id = load_current_game_id()

    for game_id, action in menu_actions_by_game_id.items():
        if game_id == current_game_id:
            action.setChecked(True)
        else:
            action.setChecked(False)


def set_check_for_auto_switch_game(action, load_auto_switch_game_status):
    action.setChecked(False)


