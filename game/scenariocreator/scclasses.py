import collections
import copy

import pbge.container
from . import scvars


class ElementDefinition(object):
    def __init__(self, name, e_type="misc", aliases=(), uid=None, **kwargs):
        # name = Human readable name; may use variables like a script block.
        # aliases = Names used to reference this element by descendant parts. Should be all-caps.
        # uid = The element's unique ID; only provided for "live" elements.
        self.name = name
        self.e_type = e_type
        self.aliases = list(aliases)
        self.etc = kwargs
        self.uid = uid


class PhysicalDefinition(object):
    def __init__(self, the_brick, element_key, parent=None, variable_keys=(), child_keys=(), **kwargs):
        # the_brick = The brick that contains this physical object; used for error checking
        # element_key = The element th is physical definition is based on; must be an element defined in this brick.
        # parent = The element this physical definition will be shown as a child of in the browser; if None or not
        #   found, this physical definition will be shown as a child of World.
        # variable_keys: Which PlotBrick variables are associated with this thing and can be edited in the thing view.
        # child_keys: Which PlotBrick child types are associated with this thing and can be edited in the thing view.
        #   If None, all of the child types will be shown in the thing view.
        self.element_key = element_key
        if element_key and element_key not in the_brick.elements:
            print("Physical Error in {}: Element {} not found".format(the_brick, element_key))
        self.parent = parent
        if parent and parent not in the_brick.elements:
            print("Physical Error in {}: Parent {} not found".format(the_brick, parent))
        self.variable_keys = set(variable_keys)
        if not self.variable_keys.issubset(the_brick.vars.keys()):
            print("Physical Error in {}: Variable keys {} not found".format(
                the_brick, self.variable_keys.difference(the_brick.vars.get_keys())
            ))
        if isinstance(child_keys, (list, tuple, set)):
            self.child_keys = set(child_keys)
            if not self.child_keys.issubset(the_brick.child_types):
                print("Physical Error in {}: Child types {} not found".format(
                    the_brick, self.child_keys.difference(the_brick.child_types)
                ))
        else:
            self.child_keys = None


class PlotBrick(object):
    # label is a string describing what sort of brick this is.
    # name is a unique identifier for this plot brick.
    # desc is a human-readable description of its function, for a certain definition of "human-readable".
    # scripts is a dict containing the scripts that will be placed in the compiled Python script.
    #    key = section name; this determines where the script will be placed.
    #    index = the block of Python code to be inserted.
    # vars: Descriptions for the user-configurable variables of this plot block.
    #    key = variable name. Should be all lowercase.
    #    value = variable description.
    # child_types: List of brick labels that can be added as children of this brick.
    # elements: Descriptions for the elements defined within this brick in dict form.
    #     Element keys should be all uppercase to differentiate them from variable identifiers
    # physicals: Descriptions for the physical objects defined within this brick in list form.
    # is_new_branch: True if this brick begins a new Plot. This is needed to check element + var inheritance.
    def __init__(
            self, label="PLOT_BLOCK", name="", display_name="", desc="", scripts=None, vars=None, child_types=(),
            elements=None, physicals=(), is_new_branch=False, sorting_rank=1000, singular=False, **kwargs
    ):
        self.label = label
        self.name = name
        self.display_name = display_name or name
        self.desc = desc
        self.scripts = dict()
        if scripts:
            self.scripts.update(scripts)
        self.vars = dict()
        if vars:
            for k, v in vars.items():
                self.vars[k] = scvars.get_variable_definition(**v)
        self.child_types = list(child_types)
        self.elements = dict()
        if elements:
            for k,v in elements.items():
                self.elements[k] = ElementDefinition(**v)
        self.physicals = [PhysicalDefinition(self, **v) for v in physicals]
        self.is_new_branch = is_new_branch
        self.sorting_rank = sorting_rank
        self.singular = singular
        self.data = kwargs.copy()

        self._format_scripts()

    def _format_scripts(self):
        if self.is_new_branch:
            aliases = list()
            for elemkey, elemdesc in self.elements.items():
                for a in elemdesc.aliases:
                    aliases.append((a, elemkey))
            element_alias_list = repr(aliases)
            self.scripts["plot_init"] = "element_alias_list = {}\n".format(element_alias_list) + self.scripts.get("plot_init", "")
        elif self.elements:
            if "plot_init" not in self.scripts:
                self.scripts["plot_init"] = ""
            for elemkey, elemdesc in self.elements.items():
                for a in elemdesc.aliases:
                    self.scripts["plot_init"] += "\nelement_alias_list.append(('{}','{}'))".format(a, elemkey)

    def get_default_vars(self):
        myvars = dict()
        for k, v in self.vars.items():
            myvars[k] = copy.copy(v.default_val)
        return myvars

    def __str__(self):
        return self.name


class BluePrint(object):
    def __init__(self, brick: PlotBrick, parent):
        if parent:
            parent.children.append(self)
        self._brick_name = brick.name
        self.brick = brick

        self.children = pbge.container.ContainerList(owner=self)
        self.raw_vars = brick.get_default_vars()
        self._uid = 0

        uvars = self.get_ultra_vars()
        for k,v in brick.elements.items():
            self.raw_vars[self.get_element_uid_var_name(k, uvars)] = self.new_element_uid()

    def get_element_uid_var_name(self, rawvarname, uvars=None):
        if not uvars:
            uvars = self.get_ultra_vars()
        return "_{}_UID".format(rawvarname.format(**uvars))

    def new_element_uid(self):
        myroot = self.get_root()
        if not hasattr(myroot, "max_element_uid"):
            myroot.max_element_uid = 0
        myroot.max_element_uid += 1
        return repr("{:0=8X}".format(myroot.max_element_uid))

    def get_save_dict(self, include_uid=True):
        mydict = dict()
        mydict["brick"] = self._brick_name
        mydict["vars"] = self.raw_vars
        mydict["children"] = list()
        if include_uid:
            mydict["uid"] = self._uid
            if hasattr(self, "max_uid"):
                mydict["max_uid"] = self.max_uid
            if hasattr(self, "max_element_uid"):
                mydict["max_element_uid"] = self.max_element_uid

        for c in self.children:
            mydict["children"].append(c.get_save_dict(include_uid))
        return mydict

    @classmethod
    def load_save_dict(cls, jdict: dict, parent=None):
        mybrick = BRICKS_BY_NAME[jdict["brick"]]
        mybp = cls(mybrick, parent)
        mybp._uid = jdict.get("uid",0)
        mybp.raw_vars.update(jdict["vars"])
        if "max_uid" in jdict:
            mybp.max_uid = jdict["max_uid"]
        if "max_element_uid" in jdict:
            mybp.max_element_uid = jdict["max_element_uid"]
        for cdict in jdict["children"]:
            cls.load_save_dict(cdict, mybp)
        mybp.sort()
        return mybp

    def copy(self):
        oldcontainer = getattr(self, "container", None)
        self.container = None
        myclone = copy.deepcopy(self)
        myclone._uid = 0
        self.container = oldcontainer
        return myclone

    def get_section(self, section_name, my_scripts, child_scripts, prefix, touched_scripts, done_scripts, used_scripts):
        if section_name in touched_scripts:
            if section_name in done_scripts:
                return done_scripts[section_name]
            else:
                print("Error: Circular Reference!")
                return ()
        else:
            touched_scripts.add(section_name)

        mys: str = my_scripts.get(section_name, "")
        for script_line in mys.splitlines():
            if script_line:
                n = script_line.find("#:")
                if n >= 0:
                    new_prefix = prefix + " " * n
                    new_section_name = script_line[n+2:].strip()
                    insert_lines = self.get_section(new_section_name, my_scripts, child_scripts, new_prefix, touched_scripts, done_scripts, used_scripts)
                    done_scripts[section_name] += insert_lines
                    used_scripts.add(new_section_name)
                else:
                    done_scripts[section_name].append(prefix + script_line)

        for script_line in child_scripts.get(section_name, ()):
            done_scripts[section_name].append(prefix + script_line)

        return done_scripts[section_name]

    def get_formatted_vars(self):
        # Get vars in the format they need to be in for output to a Python file.
        myvars = dict()
        for k,v in self.raw_vars.items():
            vardef = self.brick.vars.get(k)
            if vardef:
                myvars[k] = vardef.format_for_python(v)
            else:
                myvars[k] = v
        return myvars

    def get_ultra_vars(self):
        # Return all variables readable by this blueprint, including the _uid.
        vars = dict()
        my_ancestors = list(self.ancestors())
        my_ancestors.reverse()
        for a in my_ancestors:
            vars.update(a.get_formatted_vars())
        vars.update(self.get_formatted_vars())
        vars["_uid"] = self.uid
        return vars

    def compile(self, inherited_vars=None):
        # Return a dict of Python scripts to be added to the output file.
        # Inside the scripts, "#:" and "#>" mark places where blocks will be inserted.
        # "#:" appends the scripts from the current brick and all children.
        # "#>" just sticks the scripts from the children here, ignoring siblings + whatever.
        #    It is generally used when we need a recursive script block definition, such as a conditional "effect"
        #    block that can have children "effects".
        # Clear as mud? Good enough.
        self.sort()
        if inherited_vars:
            vars = inherited_vars.copy()
        else:
            vars = dict()
        vars.update(self.get_formatted_vars())

        ultravars = vars.copy()
        ultravars["_uid"] = self.uid

        # Add element aliases.
        elems = self.get_element_aliases()
        ultravars.update(elems)

        # Step one: collect the scripts from all children.
        mykids = collections.defaultdict(list)
        for kid in self.children:
            kid_scripts = kid.compile(inherited_vars=vars)
            for k,v in kid_scripts.items():
                mykids[k] += v

        # Step two: collect the default scripts from the brick.
        myscripts = self.brick.scripts.copy()
        for k,v in myscripts.items():
            myscripts[k] = v.format(**ultravars)

        # Step three: If any of the default scripts have slots for the kid scripts, insert those there.
        for k,v in myscripts.items():
            nuscript = list()
            for script_line in v.splitlines():
                if script_line:
                    if script_line.strip().startswith("#:"):
                        n = script_line.find("#:")
                        prefix = " " * n
                        new_section_name = script_line[n + 2:].strip()
                        if new_section_name in mykids:
                            for nuline in mykids[new_section_name]:
                                nuscript.append(prefix + nuline)
                            del mykids[new_section_name]
                        else:
                            nuscript.append(script_line)
                    elif script_line.strip().startswith("+subplot"):
                        n = script_line.find("+subplot")
                        prefix = " " * n
                        subplot_name = script_line[n + 8:].strip()
                        if subplot_name:
                            nuscript.append(
                                prefix + "self.add_sub_plot(nart, '{}', elements={})".format(
                                    subplot_name,
                                    "dict([('a', self.elements['b']) for a,b in element_alias_list])"
                                )
                            )
                        else:
                            print("Error in {}: No subplot for {}".format(self.brick.name, script_line))
                    else:
                        nuscript.append(script_line)
            myscripts[k] = "\n".join(nuscript)

        # Finally, incorporate all the rest of the scripts together.
        touchedscripts = set()
        donescripts = collections.defaultdict(list)
        usedscripts = set()
        for k in myscripts.keys():
            self.get_section(k, myscripts, mykids, "", touchedscripts, donescripts, usedscripts)

        for k in mykids.keys():
            if k not in donescripts:
                self.get_section(k, myscripts, mykids, "", touchedscripts, donescripts, usedscripts)

        for k in usedscripts:
            if k in donescripts:
                del donescripts[k]

        return donescripts

    # Gonna set up the brick as a property.
    def _get_brick(self):
        return BRICKS_BY_NAME.get(self._brick_name,None)

    def _set_brick(self,nuval):
        self._brick_name = nuval.name

    def _del_brick(self):
        self._brick_name = None

    brick = property(_get_brick,_set_brick,_del_brick)

    def _get_name(self):
        return self.brick.display_name.format(**self.get_ultra_vars())

    name = property(_get_name)

    def get_root(self):
        if hasattr(self, "container") and self.container:
            return self.container.owner.get_root()
        else:
            return self

    def ancestors(self):
        if hasattr(self, "container") and self.container:
            yield self.container.owner
            for p in self.container.owner.ancestors():
                yield p

    def predecessors(self):
        if hasattr(self, "container") and self.container:
            yield self.container.owner
            for p in self.container.owner.children:
                if p is self:
                    break
                elif not p.brick.is_new_branch:
                    yield p
            for p in self.container.owner.predecessors():
                yield p

    def _get_uid(self):
        if self._uid != 0:
            return self._uid
        else:
            myroot = self.get_root()
            if hasattr(myroot, "max_uid"):
                myroot.max_uid += 1
            else:
                myroot.max_uid = 1
            self._uid = myroot.max_uid
            return self._uid

    uid = property(_get_uid)

    def get_elements(self, uvars=None, format_keys=True):
        # Return a dict of elements accessible from this block.
        # key = element_ID
        # value = ElementDefinition
        elements = dict()
        my_ancestors = list(self.predecessors())
        my_ancestors.reverse()
        for a in my_ancestors:
            avars = a.get_ultra_vars()
            for k,v in a.brick.elements.items():
                if format_keys:
                    k = k.format(**avars)
                elements[k.format(**avars)] = ElementDefinition(v.name.format(**avars), e_type=v.e_type, uid=avars[self.get_element_uid_var_name(v.name, avars)])

        if not uvars:
            uvars = self.get_ultra_vars()
        for k,v in self.brick.elements.items():
            if format_keys:
                k = k.format(**uvars)
            elements[k] = ElementDefinition(v.name.format(**uvars), e_type=v.e_type, uid=uvars[self.get_element_uid_var_name(k, uvars)])

        return elements

    def get_element_aliases(self):
        # Return a dict of elements accessible from this block.
        # key = element alias
        # value = ELement ID
        elements = dict()
        my_ancestors = list(self.predecessors())
        my_ancestors.reverse()
        for a in my_ancestors:
            avars = a.get_ultra_vars()
            for k,v in a.brick.elements.items():
                for a in v.aliases:
                    elements[a] = k.format(**avars)

        return elements

    def get_campaign_variable_names(self, start_with_root=True):
        myset = set()
        if start_with_root:
            part = self.get_root()
        else:
            part = self
        for k,v in part.brick.vars.items():
            if v.var_type == "campaign_variable":
                myset.add(part.raw_vars.get(k,"x"))
        for p in part.children:
            myset.update(p.get_campaign_variable_names(False))
        return myset

    def sort(self):
        self.children.sort(key=lambda c: c.brick.sorting_rank)
        for c in self.children:
            c.sort()

ALL_BRICKS = list()
BRICKS_BY_LABEL = collections.defaultdict(list)
BRICKS_BY_NAME = dict()