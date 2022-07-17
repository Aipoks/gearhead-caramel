import pbge
from pbge import util
import pygame


class OptionToggler(object):
    def __init__(self, key, section="GENERAL"):
        self.key = key
        self.section = section

    def __call__(self):
        mystate = not util.config.getboolean(self.section, self.key)
        util.config.set(self.section, self.key, str(mystate))


class ConfigEditor(object):
    def __init__(self, predraw, dy=-100):
        self.dy = dy
        self.predraw = predraw

    def toggle_fullscreen(self):
        mystate = not util.config.getboolean("GENERAL", "fullscreen")
        util.config.set("GENERAL", "fullscreen", str(mystate))
        # Actually toggle the fullscreen.
        pbge.my_state.reset_screen()

    def toggle_stretchyscreen(self):
        mystate = not util.config.getboolean("GENERAL", "stretchy_screen")
        util.config.set("GENERAL", "stretchy_screen", str(mystate))
        # Actually toggle the fullscreen.
        pbge.my_state.reset_screen()

    def toggle_music(self):
        mystate = not util.config.getboolean("GENERAL", "music_on")
        util.config.set("GENERAL", "music_on", str(mystate))
        # Actually turn off or on the music.
        if mystate:
            pbge.my_state.resume_music()
        else:
            pbge.my_state.stop_music()

    def toggle_names(self):
        mystate = not util.config.getboolean("GENERAL", "names_above_heads")
        util.config.set("GENERAL", "names_above_heads", str(mystate))

    def toggle_autosave(self):
        mystate = not util.config.getboolean("GENERAL", "auto_save")
        util.config.set("GENERAL", "auto_save", str(mystate))

    def toggle_replay(self):
        mystate = not util.config.getboolean("GENERAL", "can_replay_adventures")
        util.config.set("GENERAL", "can_replay_adventures", str(mystate))

    def toggle_escape(self):
        mystate = not util.config.getboolean("GENERAL", "no_escape_from_title_screen")
        util.config.set("GENERAL", "no_escape_from_title_screen", str(mystate))

    def __call__(self):
        action = True
        while action:
            # rebuild the menu.
            mymenu = pbge.rpgmenu.Menu(-250, self.dy, 500, 200,
                                       predraw=self.predraw, font=pbge.my_state.big_font)
            mymenu.add_item("Fullscreen: {}".format(util.config.getboolean("GENERAL", "fullscreen")),
                            self.toggle_fullscreen)
            mymenu.add_item("Stretch Screen: {}".format(util.config.getboolean("GENERAL", "stretchy_screen")),
                            self.toggle_stretchyscreen)
            mymenu.add_item("Music On: {}".format(util.config.getboolean("GENERAL", "music_on")), self.toggle_music)
            mymenu.add_item("Names Above Heads: {}".format(util.config.getboolean("GENERAL", "names_above_heads")),
                            self.toggle_names)
            mymenu.add_item("Auto Save on Scene Change: {}".format(util.config.getboolean("GENERAL", "auto_save")),
                            self.toggle_autosave)
            mymenu.add_item(
                "Can Replay Adventures: {}".format(util.config.getboolean("GENERAL", "can_replay_adventures")),
                self.toggle_replay)
            mymenu.add_item(
                "No Escape from Main Menu: {}".format(util.config.getboolean("GENERAL", "no_escape_from_title_screen")),
                self.toggle_escape)
            mymenu.add_item(
                "Lancemates repaint their mecha: {}".format(util.config.getboolean("GENERAL", "lancemates_repaint_mecha")),
                OptionToggler("GENERAL", "lancemates_repaint_mecha"))

            for op in util.config.options("DIFFICULTY"):
                mymenu.add_item("{}: {}".format(op, util.config.getboolean("DIFFICULTY", op)),
                                OptionToggler(op, "DIFFICULTY"))

            mymenu.add_item("Save and Exit", False)
            if action is not True:
                mymenu.set_item_by_value(action)
            action = mymenu.query()
            if action and action is not True:
                action()

        # Export the new config options.
        with open(util.user_dir("config.cfg"), "wt") as f:
            util.config.write(f)


class PopupGameMenu(object):
    def do_quit(self, enc_or_com):
        enc_or_com.no_quit = False

    def do_config(self, enc_or_com):
        myconfigmenu = ConfigEditor(None)
        myconfigmenu()

    def __call__(self, enc_or_com):
        mymenu = pbge.rpgmenu.Menu(-150, -100, 300, 200,
                                   font=pbge.my_state.huge_font)
        mymenu.add_item("Quit Game", self.do_quit)
        mymenu.add_item("Config Options", self.do_config)
        mymenu.add_item("Continue", False)
        action = True
        while action and enc_or_com.no_quit:
            action = mymenu.query()
            if action:
                action(enc_or_com)
