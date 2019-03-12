import pbge
from pbge import widgets
import pygame
import gears
import cosplay
import backpack

LEFT_COLUMN = pbge.frects.Frect(-300,0,200,200)
CENTER_COLUMN = pbge.frects.Frect(-50,-200,200,400)
RIGHT_COLUMN = pbge.frects.Frect(175,-200,200,400)
PORTRAIT_AREA = pbge.frects.Frect(-450, -300, 400, 600)

UTIL_INFO = pbge.frects.Frect(-50,-200,300,200)
UTIL_MENU = pbge.frects.Frect(-50,50,300,150)

class MechasPilotBlock(object):
    # There should be an apostrophe in there, but y'know...
    def __init__(self, model, camp, font=None, width=220, **kwargs):
        self.model = model
        self.camp = camp
        self.width = width
        self.font = font or pbge.MEDIUMFONT
        self.update()
        self.height = self.image.get_height()
    def update(self):
        pilot = self.model.pilot
        if pilot not in self.camp.party:
            self.model.pilot = None
            pilot = None
        self.image = pbge.render_text(self.font,'Pilot: {}'.format(str(pilot)),self.width,justify=-1,color=pbge.INFO_HILIGHT)
    def render(self,x,y):
        pbge.my_state.screen.blit(self.image,pygame.Rect(x,y,self.width,self.height))

class PilotsMechaBlock(object):
    # There should be an apostrophe in there, but y'know...
    def __init__(self, model, camp, font=None, width=220, **kwargs):
        self.model = model
        self.camp = camp
        self.width = width
        self.font = font or pbge.MEDIUMFONT
        self.update()
        self.height = self.image.get_height()
    def update(self):
        mek = self.camp.get_pc_mecha(self.model)
        if mek:
            self.image = pbge.render_text(self.font,'Mecha: {}'.format(mek.get_full_name()),self.width,justify=-1,color=pbge.INFO_HILIGHT)
        else:
            self.image = pbge.render_text(self.font,'Mecha: None',self.width,justify=-1,color=pbge.INFO_HILIGHT)
    def render(self,x,y):
        pbge.my_state.screen.blit(self.image,pygame.Rect(x,y,self.width,self.height))


class CharaFHQIP(gears.info.InfoPanel):
    DEFAULT_BLOCKS = (gears.info.FullNameBlock, gears.info.ModuleStatusBlock, PilotsMechaBlock, gears.info.ExperienceBlock, gears.info.CharacterStatusBlock, gears.info.PrimaryStatsBlock, gears.info.NonComSkillBlock, gears.info.MeritBadgesBlock, gears.info.CharacterTagsBlock)

class MechaFHQIP(gears.info.InfoPanel):
    DEFAULT_BLOCKS = (gears.info.FullNameBlock, gears.info.ModuleStatusBlock, MechasPilotBlock, gears.info.MechaStatsBlock, gears.info.DescBlock)

class AssignMechaIP(gears.info.InfoPanel):
    DEFAULT_BLOCKS = (gears.info.FullNameBlock, gears.info.MechaFeaturesAndSpriteBlock)

class AssignPilotIP(gears.info.InfoPanel):
    DEFAULT_BLOCKS = (gears.info.FullNameBlock, gears.info.CharaPortraitAndSkillsBlock)

class AssignMechaDescObject(object):
    def __init__(self,camp,portrait):
        self.camp = camp
        self.portrait = portrait
        self.infoz = dict()
    def __call__(self,menu_item):
        mydest = UTIL_INFO.get_rect()
        if menu_item.value:
            if menu_item.value not in self.infoz:
                self.infoz[menu_item.value] = AssignMechaIP(model=menu_item.value,width=UTIL_INFO.w,camp=self.camp,additional_info='\n Pilot: {} \n Damage: {}%'.format(str(menu_item.value.pilot),menu_item.value.get_total_damage_status()))
            self.infoz[menu_item.value].render(mydest.x,mydest.y)

class AssignPilotDescObject(object):
    def __init__(self,camp,portrait):
        self.camp = camp
        self.portrait = portrait
        self.infoz = dict()
    def __call__(self,menu_item):
        mydest = UTIL_INFO.get_rect()
        if menu_item.value:
            if menu_item.value not in self.infoz:
                self.infoz[menu_item.value] = AssignPilotIP(model=menu_item.value,width=UTIL_INFO.w,camp=self.camp)
            self.infoz[menu_item.value].render(mydest.x,mydest.y)

class CharacterInfoWidget(widgets.Widget):
    def __init__(self,camp,pc,fhq,**kwargs):
        super(CharacterInfoWidget, self).__init__(0,0,0,0,**kwargs)
        self.camp = camp
        self.pc = pc
        self.portrait = pc.get_portrait()
        self.column = widgets.ColumnWidget(LEFT_COLUMN.dx,LEFT_COLUMN.dy,LEFT_COLUMN.w,LEFT_COLUMN.h,padding=10)
        self.children.append(self.column)
        self.column.add_interior(widgets.LabelWidget(0,0,LEFT_COLUMN.w,16,text="Inventory",justify=0,draw_border=True,on_click=self.open_backpack))
        self.column.add_interior(widgets.LabelWidget(0,0,LEFT_COLUMN.w,16,text="Assign Mecha",justify=0,draw_border=True,on_click=self.assign_mecha))
        self.column.add_interior(widgets.LabelWidget(0,0,LEFT_COLUMN.w,16,text="Change Colors",justify=0,draw_border=True,on_click=self.change_colors))
        self.fhq = fhq
        self.info = CharaFHQIP(model=pc,width=CENTER_COLUMN.w,font=pbge.SMALLFONT,camp=camp)

    def open_backpack(self,wid,ev):
        self.fhq.active = False
        myui = backpack.BackpackWidget(self.camp,self.pc)
        pbge.my_state.widgets.append(myui)
        myui.finished = False
        myui.children.append(
            pbge.widgets.LabelWidget(150, 220, 80, 16, text="Done", justify=0, on_click=self.bp_done,
                                     draw_border=True, data=myui))

        keepgoing = True
        while keepgoing and not myui.finished and not pbge.my_state.got_quit:
            ev = pbge.wait_event()
            if ev.type == pbge.TIMEREVENT:
                pbge.my_state.view()
                pbge.my_state.do_flip()
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    keepgoing = False

        pbge.my_state.widgets.remove(myui)
        pygame.event.clear()
        self.fhq.active = True

    def bp_done(self, wid, ev):
        wid.data.finished = True

    def assign_mecha(self,wid,ev):
        self.fhq.active = False

        mymenu = pbge.rpgmenu.Menu(UTIL_MENU.dx,UTIL_MENU.dy,UTIL_MENU.w,UTIL_MENU.h,font=pbge.MEDIUMFONT,predraw=self.draw_portrait)
        for mek in self.camp.party:
            if isinstance(mek, gears.base.Mecha) and mek.is_not_destroyed():
                mymenu.add_item(mek.get_full_name(),mek)
        mymenu.descobj = AssignMechaDescObject(self.camp,self.portrait)
        mek = mymenu.query()

        self.camp.assign_pilot_to_mecha(self.pc,mek)
        self.fhq.active = True

    def change_colors(self,wid,ev):
        self.fhq.active = False
        if self.pc.portrait_gen:
            cchan = self.pc.portrait_gen.color_channels
        else:
            cchan = gears.color.CHARACTER_COLOR_CHANNELS
        myui = cosplay.ColorEditor(self.pc.get_portrait(add_color=False), 0,
                                   channel_filters=cchan, colors=self.pc.colors)
        pbge.my_state.widgets.append(myui)
        myui.finished = False
        myui.children.append(
            pbge.widgets.LabelWidget(150, 220, 80, 16, text="Done", justify=0, on_click=self.color_done,
                                     draw_border=True, data=myui))

        keepgoing = True
        while keepgoing and not myui.finished and not pbge.my_state.got_quit:
            ev = pbge.wait_event()
            if ev.type == pbge.TIMEREVENT:
                pbge.my_state.view()
                pbge.my_state.do_flip()
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    keepgoing = False

        self.pc.colors = myui.colors
        self.portrait = self.pc.get_portrait(self.pc, force_rebuild=True)

        pbge.my_state.widgets.remove(myui)
        pygame.event.clear()
        self.fhq.active = True
        pbge.my_state.view.regenerate_avatars([self.pc,])

    def color_done(self, wid, ev):
        wid.data.finished = True

    def draw_portrait(self,include_background=True):
        if include_background:
            pbge.my_state.view()
        mydest = self.portrait.get_rect(0)
        mydest.midbottom = PORTRAIT_AREA.get_rect().midbottom
        self.portrait.render(mydest, 0)

    def render(self):
        self.draw_portrait(False)
        mydest = CENTER_COLUMN.get_rect()
        self.info.render(mydest.x,mydest.y)

class MechaInfoWidget(widgets.Widget):
    def __init__(self,camp,pc,fhq,**kwargs):
        super(MechaInfoWidget, self).__init__(0,0,0,0,**kwargs)
        self.camp = camp
        self.pc = pc
        self.portrait = pc.get_portrait()
        self.info = MechaFHQIP(model=pc,width=CENTER_COLUMN.w,camp=camp,font=pbge.SMALLFONT)
        self.column = widgets.ColumnWidget(LEFT_COLUMN.dx,LEFT_COLUMN.dy,LEFT_COLUMN.w,LEFT_COLUMN.h,padding=10)
        self.children.append(self.column)
        self.column.add_interior(widgets.LabelWidget(0,0,LEFT_COLUMN.w,16,text="Inventory",justify=0,draw_border=True,on_click=self.open_backpack))
        self.column.add_interior(widgets.LabelWidget(0,0,LEFT_COLUMN.w,16,text="Assign Pilot",justify=0,draw_border=True,on_click=self.assign_pilot))
        self.column.add_interior(widgets.LabelWidget(0,0,LEFT_COLUMN.w,16,text="Change Colors",justify=0,draw_border=True,on_click=self.change_colors))
        self.fhq = fhq

    def draw_portrait(self,include_background=True):
        if include_background:
            pbge.my_state.view()
        mydest = self.portrait.get_rect(0)
        mydest.midbottom = PORTRAIT_AREA.get_rect().midbottom
        self.portrait.render(mydest, 0)

    def render(self):
        self.draw_portrait(False)
        mydest = CENTER_COLUMN.get_rect()
        self.info.render(mydest.x,mydest.y)

    def assign_pilot(self,wid,ev):
        self.fhq.active = False

        mymenu = pbge.rpgmenu.Menu(UTIL_MENU.dx,UTIL_MENU.dy,UTIL_MENU.w,UTIL_MENU.h,font=pbge.MEDIUMFONT,predraw=self.draw_portrait)
        for plr in self.camp.party:
            if isinstance(plr, gears.base.Character) and plr.is_not_destroyed():
                mymenu.add_item(plr.get_full_name(),plr)
        mymenu.descobj = AssignPilotDescObject(self.camp,self.portrait)
        pilot = mymenu.query()

        self.camp.assign_pilot_to_mecha(pilot,self.pc)
        self.fhq.active = True

    def open_backpack(self,wid,ev):
        self.fhq.active = False
        myui = backpack.BackpackWidget(self.camp,self.pc)
        pbge.my_state.widgets.append(myui)
        myui.finished = False
        myui.children.append(
            pbge.widgets.LabelWidget(150, 220, 80, 16, text="Done", justify=0, on_click=self.bp_done,
                                     draw_border=True, data=myui))

        keepgoing = True
        while keepgoing and not myui.finished and not pbge.my_state.got_quit:
            ev = pbge.wait_event()
            if ev.type == pbge.TIMEREVENT:
                pbge.my_state.view()
                pbge.my_state.do_flip()
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    keepgoing = False

        pbge.my_state.widgets.remove(myui)
        pygame.event.clear()
        self.fhq.active = True

    def bp_done(self, wid, ev):
        wid.data.finished = True


    def change_colors(self,wid,ev):
        self.fhq.active = False
        myui = cosplay.ColorEditor(self.pc.get_portrait(add_color=False), 0,
                                   channel_filters=gears.color.MECHA_COLOR_CHANNELS, colors=self.pc.colors)
        pbge.my_state.widgets.append(myui)
        myui.finished = False
        myui.children.append(
            pbge.widgets.LabelWidget(150, 220, 80, 16, text="Done", justify=0, on_click=self.color_done,
                                     draw_border=True, data=myui))

        keepgoing = True
        while keepgoing and not myui.finished and not pbge.my_state.got_quit:
            ev = pbge.wait_event()
            if ev.type == pbge.TIMEREVENT:
                pbge.my_state.view()
                pbge.my_state.do_flip()
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    keepgoing = False

        self.pc.colors = myui.colors
        self.portrait = self.pc.get_portrait(self.pc, force_rebuild=True)

        pbge.my_state.widgets.remove(myui)
        pygame.event.clear()
        self.fhq.active = True
        pbge.my_state.view.regenerate_avatars([self.pc,])

    def color_done(self, wid, ev):
        wid.data.finished = True


class PartyMemberButton(widgets.Widget):
    def __init__(self,camp,pc,fhq,**kwargs):
        super(PartyMemberButton, self).__init__(0,0,RIGHT_COLUMN.w,72,**kwargs)
        self.camp = camp
        self.pc = pc
        self.fhq = fhq
        self.avatar_pic = pc.get_sprite()
        self.avatar_frame = pc.frame
    def render(self):
        mydest = self.get_rect().inflate(-8,-8)
        if self.pc is self.fhq.active_pc:
            widgets.widget_border_on.render(mydest)
        else:
            widgets.widget_border_off.render(mydest)
        self.avatar_pic.render(mydest,self.avatar_frame)
        mydest.x += 64
        mydest.w -= 64
        pbge.draw_text(pbge.MEDIUMFONT,self.pc.get_full_name(),mydest,color=pbge.WHITE)

class FieldHQ(widgets.Widget):
    # Three columns
    # To the left: the character portrait (if available)
    # In the center: the character info/action widgets
    # To the right: The list of characters/mecha in the party
    def __init__(self,camp):
        super(FieldHQ, self).__init__(0,0,0,0)

        self.up_button = widgets.ButtonWidget(0,0,RIGHT_COLUMN.w,16,sprite=pbge.image.Image("sys_updownbuttons.png",128,16),off_frame=1)
        self.down_button = widgets.ButtonWidget(0,0,RIGHT_COLUMN.w,16,sprite=pbge.image.Image("sys_updownbuttons.png",128,16),frame=2,on_frame=2,off_frame=3)

        self.member_selector = widgets.ScrollColumnWidget(0,0,RIGHT_COLUMN.w,RIGHT_COLUMN.h-42,up_button = self.up_button,down_button=self.down_button)

        self.r_column = widgets.ColumnWidget(RIGHT_COLUMN.dx,RIGHT_COLUMN.dy,RIGHT_COLUMN.w,RIGHT_COLUMN.h)
        self.r_column.add_interior(self.up_button)
        self.r_column.add_interior(self.member_selector)
        self.r_column.add_interior(self.down_button)

        self.children.append(self.r_column)

        self.member_widgets = dict()

        for pc in camp.party:
            self.member_selector.add_interior(PartyMemberButton(camp,pc,fhq=self,on_click=self.click_member))
            if isinstance(pc,gears.base.Character):
                self.member_widgets[pc] = CharacterInfoWidget(camp,pc,self,active=False)
                self.children.append(self.member_widgets[pc])
            elif isinstance(pc,gears.base.Mecha):
                self.member_widgets[pc] = MechaInfoWidget(camp,pc,self,active=False)
                self.children.append(self.member_widgets[pc])

        self.camp = camp
        self.finished = False
        self.active_pc = camp.pc
        self.active_widget = self.member_widgets.get(camp.pc,None)
        if self.active_widget:
            self.active_widget.active = True

    def click_member(self,wid,ev):
        if self.active_widget:
            self.active_widget.active = False
        self.active_widget = self.member_widgets.get(wid.pc,None)
        self.active_pc = wid.pc
        if self.active_widget:
            self.active_widget.active = True

    def done_button(self,wid,ev):
        if not pbge.my_state.widget_clicked:
            self.finished = True

    @classmethod
    def create_and_invoke(cls, camp):
        # Run the UI. Return a DoInvocation action if an invocation
        # was chosen, or None if the invocation was cancelled.
        myui = cls(camp)
        pbge.my_state.widgets.append(myui)
        myui.children.append(pbge.widgets.LabelWidget(150,220,80,16,text="Done",justify=0,on_click=myui.done_button,draw_border=True))

        keepgoing = True
        while keepgoing and not myui.finished and not pbge.my_state.got_quit:
            ev = pbge.wait_event()
            if ev.type == pbge.TIMEREVENT:
                pbge.my_state.view()
                pbge.my_state.do_flip()
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    keepgoing = False

        pbge.my_state.widgets.remove(myui)
