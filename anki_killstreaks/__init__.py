# -*- coding: utf-8 -*-
#
# Entry point for the add-on into Anki
# Please do not edit this if you do not know what you are doing.
# Original copywrite statement
# -------
# Copyright: (c) 2017 Glutanimate <https://glutanimate.com/>
# License: GNU AGPLv3 <https://www.gnu.org/licenses/agpl.html>
# -------
# Modifications by jac241 <https://github.com/jac241> for Anki Killstreaks addon

import os

try:
    os.environ['IN_TEST_SUITE']
except KeyError:
    from . import main
