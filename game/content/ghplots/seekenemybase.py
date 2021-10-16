from pbge.plots import Plot, PlotState, Rumor
import game
import gears
import pbge
import pygame
import random
from game import teams,ghdialogue
from game.content import gharchitecture,ghterrain,ghwaypoints,plotutility,ghcutscene
from pbge.dialogue import Offer, ContextTag, Reply
from game.ghdialogue import context
from game.content.ghcutscene import SimpleMonologueDisplay
from game.content import adventureseed
from . import missionbuilder, rwme_objectives, campfeatures
from game.memobrowser import Memo

SEEK_ENEMY_BASE_MISSION = "SEEK_ENEMY_BASE_MISSION"
AUTOFIND_ENEMY_BASE_MISSION = "AUTOFIND_ENEMY_BASE_MISSION"
SEBO_SEARCH_FOR_BASE = "SEBO_SEARCH_FOR_BASE"

#   *************************
#   ***  SEEK_ENEMY_BASE  ***
#   *************************
#
# You need to find an enemy base. This plot will load subplots until the base is found or the game runs out of
# patience, whichever comes first. Note that the enemy base need not necessarily be an actual base- it's a location
# or thing that the provided enemy faction knows the location of but you don't.
#
# This plot will set a WIN trigger when the base (or whatever) is located.
#
# Needed Elements:
# METROSCENE, METRO, MISSION_GATE
# ENEMY_FACTION
# ENEMY_BASE_NAME: The name to be used for the enemy base.
#

class SeekEnemyBaseMain(campfeatures.MetrosceneRandomPlotHandler):
    LABEL = "SEEK_ENEMY_BASE"

    MAX_PLOTS = 1
    SUBPLOT_LABEL = SEEK_ENEMY_BASE_MISSION

    def custom_init( self, nart ):
        print(self.elements["METROSCENE"])
        ok = super().custom_init(nart)
        if ok:
            self.mission_patience = random.randint(1,2)
            self.rank_modifier = 0
            self.elements["WIN_FUN"] = self.locate_the_base
            self.elements["SEMIWIN_FUN"] = self.win_a_mission
        return ok

    def locate_the_base(self, camp: gears.GearHeadCampaign):
        camp.check_trigger("WIN", self)
        self.adv.end_adventure(camp)

    def win_a_mission(self, camp):
        self.rank_modifier += random.randint(1, 3)
        self.mission_patience -= 1
        if self.active and self.mission_patience < 1:
            self.subplots["MISSION"] = game.content.load_dynamic_plot(
                camp, AUTOFIND_ENEMY_BASE_MISSION, PlotState(rank=self.rank + self.rank_modifier).based_on(self)
            )

    def _get_dialogue_grammar(self, npc: gears.base.Character, camp):
        mygram = dict()
        if npc.faction is not self.elements.get("ENEMY_FACTION"):
            mygram["[News]"] = ["only {ENEMY_FACTION} know where {ENEMY_BASE_NAME} is".format(**self.elements), ]
        return mygram

    def calc_rank(self, camp: gears.GearHeadCampaign):
        return self.rank + self.rank_modifier


#   *********************************
#   ***  SEEK_ENEMY_BASE_MISSION  ***
#   *********************************
#
# Elements:
# WIN_FUN = A function with signature (camp) to call when the enemy base is located.
# SEMIWIN_FUN = A function with signature (camp) to call when a mission is "won", but base not located.
#

class BasicCombatBaseSearch(Plot):
    LABEL = SEEK_ENEMY_BASE_MISSION
    active = True
    scope = "METRO"

    RUMOR = Rumor(
        "{NPC} lost a fight to {ENEMY_FACTION}",
        offer_msg="You can ask {NPC} about {ENEMY_FACTION} yourself; speak to {NPC.gender.object_pronoun} at {NPC_SCENE}.",
        memo="{NPC} lost a battle against {ENEMY_FACTION}.", prohibited_npcs=("NPC",)
    )

    def custom_init( self, nart ):
        npc = self.seek_element(nart, "NPC", self.is_good_npc, scope=self.elements["METROSCENE"])
        self.elements["NPC_SCENE"] = npc.scene
        print(npc.scene)
        sgen, archi = gharchitecture.get_mecha_encounter_scenegen_and_architecture(self.elements["METROSCENE"])
        self.mission_seed = missionbuilder.BuildAMissionSeed(
            nart.camp, "Fight {}".format(self.elements["ENEMY_FACTION"]),
            self.elements["METROSCENE"], self.elements["MISSION_GATE"],
            self.elements["ENEMY_FACTION"], npc.faction, self.rank,
            objectives=(missionbuilder.BAMO_LOCATE_ENEMY_FORCES,),
            scenegen=sgen, architecture=archi, on_win=self.elements["SEMIWIN_FUN"],
        )
        self.mission_active = False
        return True

    def is_good_npc(self, nart, candidate):
        return (
            isinstance(candidate, gears.base.Character) and candidate.combatant and
            not nart.camp.are_faction_allies(candidate, self.elements["ENEMY_FACTION"])
        )

    def NPC_offers(self, camp):
        mylist = list()
        if not self.mission_active:
            pass
        return mylist


#   *************************************
#   ***  AUTOFIND_ENEMY_BASE_MISSION  ***
#   *************************************

class InsultinglyEasyAutofindEnemyBase(Plot):
    LABEL = AUTOFIND_ENEMY_BASE_MISSION
    active = True
    scope = "METRO"

    def t_UPDATE(self, camp: gears.GearHeadCampaign):
        pbge.alert("You find a piece of paper on the ground with the location of {ENEMY_BASE_NAME} written on it.".format(**self.elements))
        self.elements["WIN_FUN"](camp)
        self.end_plot(camp)

#   ******************************
#   ***  SEBO_SEARCH_FOR_BASE  ***
#   ******************************
#
# This objective can be added to any mission to give a chance that the lance will locate the base being sought.
# The skills known by the party members will determine whether or not the base is found.
#
# Needed Elements:
# FIND_BASE_FUN: A function with signature (camp) to call if the base is found.
#

class DDBAMOSearchForBase( Plot ):
    LABEL = SEBO_SEARCH_FOR_BASE
    active = True
    scope = "LOCALE"
    def custom_init( self, nart ):
        self.intro_ready = True
        return True

    def LOCALE_ENTER(self,camp: gears.GearHeadCampaign):
        if self.intro_ready:
            self.intro_ready = False
            candidates = list()
            if camp.party_has_skill(gears.stats.Scouting):
                candidates.append(self.attempt_scouting)
            if camp.party_has_skill(gears.stats.Stealth):
                candidates.append(self.attempt_stealth)
            if camp.party_has_skill(gears.stats.Wildcraft):
                candidates.append(self.attempt_wildcraft)
            if candidates:
                random.choice(candidates)(camp)

    def t_END(self, camp):
        pass

    def attempt_scouting(self,camp):
        pc = camp.make_skill_roll(gears.stats.Perception,gears.stats.Scouting,self.rank)
        if pc:
            if pc.get_pilot() is camp.pc:
                mymenu = ghcutscene.PromptMenu("You detect hostile mecha on the road ahead. They are still far enough away that you can avoid them if you want to.")
            else:
                mymenu = ghcutscene.SimpleMonologueMenu("[I_HAVE_DETECTED_ENEMIES] [WE_CAN_AVOID_COMBAT]",pc,camp)
            mymenu.add_item("Avoid them",self.cancel_the_adventure)
            mymenu.add_item("Engage them",None)
            go = mymenu.query()
            if go:
                go(camp)

    def attempt_stealth(self,camp):
        pc = camp.make_skill_roll(gears.stats.Perception,gears.stats.Stealth,self.rank)
        if pc:
            if pc.get_pilot() is camp.pc:
                mymenu = ghcutscene.PromptMenu("You encounter a group of hostile mecha, but manage to remain unseen.")
            else:
                mymenu = ghcutscene.SimpleMonologueMenu("[ENEMIES_HAVE_NOT_DETECTED_US] [WE_CAN_AVOID_COMBAT]",pc,camp)
            mymenu.add_item("Avoid them",self.cancel_the_adventure)
            mymenu.add_item("Engage them",None)
            go = mymenu.query()
            if go:
                go(camp)

    def attempt_wildcraft(self,camp):
        pc = camp.make_skill_roll(gears.stats.Perception,gears.stats.Wildcraft,self.rank)
        if pc:
            if pc.get_pilot() is camp.pc:
                mymenu = ghcutscene.PromptMenu("You find tracks belonging to enemy mecha. It would be a simple matter to find an alternate route around them.")
            else:
                mymenu = ghcutscene.SimpleMonologueMenu("[THERE_ARE_ENEMY_TRACKS] [WE_CAN_AVOID_COMBAT]",pc,camp)
            mymenu.add_item("Avoid them",self.cancel_the_adventure)
            mymenu.add_item("Engage them",None)
            go = mymenu.query()
            if go:
                go(camp)

    def find_the_base(self,camp: gears.GearHeadCampaign):

        self.adv.cancel_adventure(camp)
