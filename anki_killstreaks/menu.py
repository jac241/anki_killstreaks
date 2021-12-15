from functools import partial
import webbrowser
from aqt.qt import QMenu

from .game import (
    load_current_game_id,
    set_current_game_id,
    toggle_auto_switch_game,
    load_auto_switch_game_status,
)
from . import profile_settings, networking, chase_mode


def connect_menu(main_window, profile_controller, network_thread):
    # probably overdoing it with partial functions here... but none of these
    # need to be classes honestly
    top_menu = QMenu("&Killstreaks", main_window)
    game_menu = QMenu("Select Game", main_window)

    leaderboard_action = top_menu.addAction("&Donate with Cash App: $jac241")
    leaderboard_action.triggered.connect(
        lambda: webbrowser.open("https://cash.app/$jac241")
    )

    leaderboard_action = top_menu.addAction("&Donate with Venmo: @jac241")
    leaderboard_action.triggered.connect(
        lambda: webbrowser.open("https://venmo.com/jac241")
    )

    halo_3_action = game_menu.addAction("Halo 3")
    halo_3_action.setCheckable(True)
    halo_3_action.triggered.connect(
        partial(
            set_current_game_id,
            game_id="halo_3",
            get_settings_repo=profile_controller.get_settings_repo,
            on_game_changed=profile_controller.change_game,
        )
    )

    mw2_action = game_menu.addAction("Call of Duty: Modern Warfare 2")
    mw2_action.setCheckable(True)
    mw2_action.triggered.connect(
        partial(
            set_current_game_id,
            game_id="mw2",
            get_settings_repo=profile_controller.get_settings_repo,
            on_game_changed=profile_controller.change_game,
        )
    )

    halo_5_action = game_menu.addAction("Halo 5")
    halo_5_action.setCheckable(True)
    halo_5_action.triggered.connect(
        partial(
            set_current_game_id,
            game_id="halo_5",
            get_settings_repo=profile_controller.get_settings_repo,
            on_game_changed=profile_controller.change_game,
        )
    )
    halo_infinite_action = game_menu.addAction("Halo Infinite")
    halo_infinite_action.setCheckable(True)
    halo_infinite_action.triggered.connect(
        partial(
            set_current_game_id,
            game_id="halo_infinite",
            get_settings_repo=profile_controller.get_settings_repo,
            on_game_changed=profile_controller.change_game,
        )
    )

    vanguard_action = game_menu.addAction("Call of Duty: Vanguard")
    vanguard_action.setCheckable(True)
    vanguard_action.triggered.connect(
        partial(
            set_current_game_id,
            game_id="vanguard",
            get_settings_repo=profile_controller.get_settings_repo,
            on_game_changed=profile_controller.change_game,
        )
    )

    mwr_action = game_menu.addAction("Call of Duty: Modern Warfare Remastered")
    mwr_action.setCheckable(True)
    mwr_action.triggered.connect(
        partial(
            set_current_game_id,
            game_id="mwr",
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
                halo_infinite=halo_infinite_action,
                vanguard=vanguard_action,
                mwr=mwr_action,
            ),
            load_current_game_id=partial(
                load_current_game_id,
                get_settings_repo=profile_controller.get_settings_repo,
            ),
        )
    )

    auto_switch_game_action = top_menu.addAction("&Automatically Switch Games")
    auto_switch_game_action.setCheckable(True)
    auto_switch_game_action.triggered.connect(
        partial(
            toggle_auto_switch_game,
            get_settings_repo=profile_controller.get_settings_repo,
            on_auto_switch_game_toggled=profile_controller.on_auto_switch_game_toggled,
        )
    )

    top_menu.aboutToShow.connect(
        partial(
            set_check_for_auto_switch_game,
            action=auto_switch_game_action,
            load_auto_switch_game_status=partial(
                load_auto_switch_game_status,
                get_settings_repo=profile_controller.get_settings_repo,
            ),
        )
    )
    leaderboard_action = top_menu.addAction("&Leaderboards")
    leaderboard_action.triggered.connect(
        lambda: webbrowser.open(networking.sra_base_url)
    )

    profile_settings_action = top_menu.addAction("&Profile settings...")
    profile_settings_action.triggered.connect(
        lambda: profile_settings.show_dialog(
            main_window,
            network_thread,
            profile_controller.get_user_repo(),
            profile_controller.get_achievements_repo(),
        )
    )

    chase_mode_action = top_menu.addAction("&Chase mode")
    chase_mode_action.setCheckable(True)
    chase_mode_action.triggered.connect(
        partial(
            chase_mode.toggle_chase_mode,
            profile_controller=profile_controller,
            main_window=main_window,
        )
    )
    top_menu.aboutToShow.connect(
        partial(
            set_check_for_show_chase_mode,
            action=chase_mode_action,
            get_settings_repo=profile_controller.get_settings_repo,
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
    action.setChecked(load_auto_switch_game_status())


def set_check_for_show_chase_mode(action, get_settings_repo):
    action.setChecked(get_settings_repo().should_show_chase_mode)
