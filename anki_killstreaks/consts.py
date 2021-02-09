# -*- coding: utf-8 -*-

"""
This file is part of the Puppy Reinforcement add-on for Anki.

Global variables

Copyright: (c) 2018 Glutanimate <https://glutanimate.com/>
License: GNU AGPLv3 <https://www.gnu.org/licenses/agpl.html>
"""

import sys
import os

anki21 = True

if not (os.environ.get("KILLSTREAKS_ENV", "production") == "test"):
    from anki import version
    anki21 = version.startswith("2.1.")

sys_encoding = sys.getfilesystemencoding()

if anki21:
    addon_path = os.path.dirname(__file__)
else:
    addon_path = os.path.dirname(__file__).decode(sys_encoding)
