import json
from functools import lru_cache
from pathlib import Path

THIS_ADDON_PATH = Path(__file__).parent.absolute()
ALL_ADDONS_PATH = THIS_ADDON_PATH.parent


@lru_cache
def is_installed_and_enabled(addon_name, addons_dir_path=ALL_ADDONS_PATH):
    metas = []
    for metafile in addons_dir_path.glob("**/meta.json"):
        with open(metafile, "r") as f:
            metas.append(json.load(f))

    def addon_installed_and_enabled(addon_name, meta):
        return meta.get('name', '') == addon_name and not meta.get('disabled', False)

    return any(addon_installed_and_enabled(addon_name, meta) for meta in metas)



