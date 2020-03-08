# Anki Killstreaks

A Halo and Call of Duty inspired add-on that makes doing your reviews more bearable.

## Demo
![anki killstreaks demo 2](https://user-images.githubusercontent.com/3792672/76172087-71164780-6168-11ea-8ab0-8962ec2b74c5.gif)

<details>

<summary><i>More Screenshots</i></summary>

Deck Browser:

![deck browser](https://user-images.githubusercontent.com/3792672/76172100-9c993200-6168-11ea-8480-af9ddd8ee8df.png)

Deck Overview:

![deck overview](https://user-images.githubusercontent.com/3792672/76172101-9d31c880-6168-11ea-8fc2-e2ee63966c0f.png)

Statistics Page:

![Statistics overview](https://user-images.githubusercontent.com/3792672/76172103-9d31c880-6168-11ea-8f8b-1ce85b2d3403.png)

Killstreak menu options:

![Killstreaks menu](https://user-images.githubusercontent.com/3792672/76172102-9d31c880-6168-11ea-8a51-ecc61f074783.png)

</details>

### The Add-on

Everyone who has used Anki for studying knows it's big drawback, reviewing takes forever and is pretty boring. This add-on seeks to address this by given reinforcement and incentive to get through reviews quickly. As you answer cards within 8 seconds of each other, you will rack up "multikills". Double Kill, Triple Kill, etc. all the way up to Killionaire. The more cards you answer with good, easy, or hard in a row, the more progress you'll make towards the best killstreaks, Perfection (50 in a row) for the Halo games, and the Tactical Nuke (25 in a row) for MW2.

One added feature in version 1.0.0 is the auto switch game setting. Once you've acheived all of the medals for a given game without closing Anki, it will advance you to the next game. This helps push you to focus and answer the cards correctly.

#### Features:
- Your favorite Halo3, Call of Duty: MW2, and Halo 5 kill streaks
  - Double Kill, Triple Kill, Overkill, Chopper Gunner, Tactical Nuke, etc.
- See the medals you earned today for each game on the Deck Browser screen
- See the medals earned today for a given deck in the Deck Overview screen
- Browse all the medals you've earned within the Stats window

### Known Limitations
- Undoing and redoing a card will add to the streak
  - The fix for this is outlined in the controllers.py file. I just don't have time to implement it (Step 1 is looming)
- Pressing 2, 3, or 4 on question side of a card will add to the streak
  - This happens due to support for the right hand reviews add-on, which adds ability to advance cards without showing the answer. If this one bugs you, you're free to submit a pull-request and I will merge it in. 
- Medals don't sync between computers
  - Not going to happen unless someone pays me lots of $$$
- I chose the killstreaks for MW2, so if you really wanted Counter-UAV you're out of luck. You can change it and submit a pull request with an interface to choose them if you want.


### Reporting issues
Please report issues through [Github](https://github.com/jac241/anki_killstreaks/issues). Include a description of what you were doing, the error message shown in Anki, and a screenshot if possible.

### Contributing

Contributing is definitely welcome. Submit a pull request with your changes. I generally stick to 80-column and PEP8 standards, and I prefer everything not touching Qt to be snake_case. If the changes you're making introduce complex logic, tests would be helpful. I use pytest.

### Special Thanks
Special thanks to Glutaminate, who has taken Anki to the next level.
Extra special thanks to Glutaminate for [this question](https://stackoverflow.com/questions/52538252/import-vendored-dependencies-in-python-package-without-modifying-sys-path-or-3rd) on StackOverflow, and to Martijn Pieters for answering. Wow that saved me so much time...

### License and Credits

*Anki Killstreaks* is *Copyright © 2019 James Castiglione (jac241)*

Part of this add-on is based on the Puppy Reinforcement add-on by Glutaminate. Copyright for Puppy Reinforcement:

-----
Copyright: (c) Glutanimate 2016-2018 <https://glutanimate.com/>
License: GNU AGPLv3 or later <https://www.gnu.org/licenses/agpl.html>

-----

Anki Killstreaks is free and open-source software. The add-on code that runs within Anki is released under the GNU AGPLv3 license, extended by a number of additional terms. For more information please see the [LICENSE](https://github.com/jac241/anki_killstreaks/blob/master/LICENSE) file that accompanied this program.

Distributed WITHOUT ANY WARRANTY.
