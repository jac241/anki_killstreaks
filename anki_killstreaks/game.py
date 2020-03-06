def load_current_game_id(get_settings_repo):
    return get_settings_repo().current_game_id


def set_current_game_id(game_id, get_settings_repo, on_game_changed):
    get_settings_repo().current_game_id = game_id
    on_game_changed(game_id=game_id)


def toggle_auto_switch_game(get_settings_repo, on_auto_switch_game_toggled):
    should_auto_switch_game = get_settings_repo().toggle_auto_switch_game()
    on_auto_switch_game_toggled(should_auto_switch_game=should_auto_switch_game)
