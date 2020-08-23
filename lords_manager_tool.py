#!/usr/bin/env python

import os
import string
import shelve
import tkinter as tk
import tkinter.filedialog as fd

from dbm import error
from functools import partial
from typing import Any, Iterable
from tkinter import (
    DISABLED, NORMAL, BOTH, TOP, LEFT, RIGHT, BOTTOM, HORIZONTAL, VERTICAL,
    CENTER, END, IntVar, StringVar, Label, Entry, Spinbox, Listbox, Frame,
    LabelFrame, ACTIVE, SUNKEN, Button as TkButton
    )
from functions import load_image_or_placeholder, plural, single_slashes
from classes import *
from lords_manager import LordsManager

WINDOW_TITLE = 'Lords Manager'


def pack_widget(widget, **kwargs):
    """Pack widgets and nested widgets recursively."""
    # assert isinstance(widget, (tk.Widget, List))
    try:
        widget.pack(**kwargs)
    except AttributeError:
        return [pack_widget(w, **kwargs) for w in widget]
    return widget


class User:
    admin = '87@fei-hf37#yr3of_8'

    auth_file = 'admin.auth' if os.path.exists('user.auth') else 'user.auth'
    with shelve.open(auth_file, 'w') as file:
        user = file['user']
    superuser = user == admin

    @classmethod
    def new_user(cls):
        with shelve.open('user.auth', 'c') as file:
            file['user'] = ''.join(
                [choice(string.ascii_lowercase + string.digits)
                    for i in range(32)])


class AuthButton(tk.Button):

    def __init__(self, master=None, cnf={}, **kw):
        super().__init__(master, cnf, **kw)
        self.configure(state=NORMAL if User.superuser else DISABLED)


class AuthListbox(Listbox):

    def __init__(self, master=None, cnf={}, **kw):
        super().__init__(master, cnf, **kw)
        self.configure(state=NORMAL if User.superuser else DISABLED)


class Application(tk.Tk):

    def __init__(self):
        super().__init__()
        self.wm_title(WINDOW_TITLE)

        self.manager = LordsManager()
        self.sections: Dict[str, tk.LabelFrame]

        # --- Variables ---
        self.lords_count = IntVar()
        self.lords_female = IntVar()
        self.lords_male = IntVar()
        self.royalists = IntVar()
        self.nationalists = IntVar()
        self.neutral = IntVar()
        self.military = IntVar()
        self.clergy = IntVar()
        self.lords_by_titles: Dict[Title, IntVar] = {
            t: IntVar() for i, t in enumerate(Title)
            }
        self.lords_list_title = StringVar(value='Lords:')
        # --- Locations ---
        self.locations_count = IntVar()
        self.locations_by_type: Dict[LocationType, IntVar] = {
            loc: IntVar() for i, loc in enumerate(LocationType)
            }
        self.locations_list_title = StringVar()
        # these filters are used to filter lords and locations in listboxes:
        self.lords_filter = None
        self.locations_filter = None

        # ---- Sections of the Window ----
        sections_names = ['Lords in numbers:', 'Locations in numbers:',
                          'Actions:', 'Lords and fiefs:']
        self.sections = {
            name: LabelFrame(self,
                             text=name,
                             labelanchor='n') for name in sections_names}

        # ---- Sections content ----
        self.create_lords_in_numbers_section()
        self.create_locations_in_numbers_section()
        self.create_actions_section()
        self.create_lords_and_fiefs_section()

        self.load_data()

        for section in self.sections.values():
            section.pack(fill=BOTH, expand=False, side=TOP)

    def create_lords_in_numbers_section(self):
        """"""
        section = self.sections['Lords in numbers:']
        column, row = Counter(), Counter()
        # first row:
        label = Label(section, text='Lords total:')
        label.bind('<Button-1>', partial(self.change_lords_filter, None))
        label.grid(column=column(), row=row.next())
        lords_counter = Entry(
            section, textvariable=self.lords_count, width=4,
            disabledbackground='white',
            disabledforeground='black', state=DISABLED, justify=CENTER
            ).grid(column=column.next(), row=row())
        for title, value in self.lords_by_titles.items():
            label = Label(section, text=f'{plural(title.value).title()}:')
            label.grid(column=column.next(), row=row())
            label.bind('<Button-1>', partial(self.change_lords_filter, title))
            Entry(section, textvariable=value, width=4,
                  disabledbackground='white', disabledforeground='black',
                  state=DISABLED, justify=CENTER
                  ).grid(column=column.next(), row=row())
        # second row:
        column.restart()
        Label(section, text='Men:').grid(column=column(), row=row.next())
        Entry(section, textvariable=self.lords_male, width=4,
              disabledbackground='white', disabledforeground='black',
              state=DISABLED, justify=CENTER
              ).grid(column=column.next(), row=row())
        Label(section, text='Women:').grid(column=column.next(), row=row())
        Entry(section, textvariable=self.lords_female, width=4,
              disabledbackground='white', disabledforeground='black',
              state=DISABLED, justify=CENTER
              ).grid(column=column.next(), row=row())
        Label(section, text='Clergy:').grid(column=column.next(), row=row())
        Entry(section, textvariable=self.clergy, width=4,
              disabledbackground='white', disabledforeground='black',
              state=DISABLED, justify=CENTER
              ).grid(column=column.next(), row=row())
        Label(section, text='Military officers:').grid(column=column.next(),
                                                       row=row())
        Entry(section, textvariable=self.military, width=4,
              disabledbackground='white', disabledforeground='black',
              state=DISABLED, justify=CENTER).grid(column=column.next(),
                                                   row=row())
        factions = (self.royalists, self.nationalists, self.neutral)

        for i, faction in enumerate(Faction):
            label = Label(section, text=f'{faction.value.title()}:')
            label.bind('<Button-1>',
                       partial(self.change_lords_filter, faction))
            label.grid(column=column.next(), row=row())
            Entry(section, textvariable=factions[i], width=3,
                  disabledbackground='white', justify=CENTER,
                  disabledforeground='black', state=DISABLED).grid(
                column=column.next(), row=row())

    def create_locations_in_numbers_section(self):
        """Display numbers of Lords of different categories."""
        section = self.sections['Locations in numbers:']
        column, row = Counter(), Counter()
        # first row:
        Label(section, text='Locations total:').grid(column=column.next(),
                                                     row=row.next())
        self.locations_counter = Entry(
            section, textvariable=self.locations_count, width=4,
            disabledbackground='white',
            disabledforeground='black', state=DISABLED, justify=CENTER
            ).grid(column=column.next(), row=row())
        for location, value in self.locations_by_type.items():
            if column() == 18:
                column.restart()
                row.next()
            label = Label(section, text=f'{plural(location.value).title()}:')
            label.grid(column=column.next(), row=row())
            label.bind('<Button-1>',
                       partial(self.change_locations_filter, location))
            Entry(section, textvariable=value, width=3,
                  disabledbackground='white',
                  disabledforeground='black', state=DISABLED, justify=CENTER
                  ).grid(column=column.next(), row=row())

    def create_actions_section(self):
        """Display numbers of Locations of different types."""
        section = self.sections['Actions:']

        AuthButton(section, command=partial(self.details_window, Nobleman(
                   'ADD NAME!', 25, RAGADAN)), text='Add new lord',
                   state=self.sdb_file_exists()).pack(side=LEFT)

        TkButton(section, command=self.load_data, text='Reload data',
                 state=self.sdb_file_exists()).pack(side=LEFT, padx=380)

        AuthButton(section, command=partial(self.details_window,
                   Location('ADD NAME!')), text='Add new location',
                   state=self.sdb_file_exists()).pack(side=RIGHT)

    def create_lords_and_fiefs_section(self):
        """
        In this section two lists re displayed: Lords on the left and Locations on the right
        side of the window. In the middle a picture of currently selected object and button
        opening detail-view is displayed.
        """
        section = self.sections['Lords and fiefs:']
        left_frame = Frame(section)
        center_frame = Frame(section)
        right_frame = Frame(section)

        lords_list_label = Label(left_frame,
                                 textvariable=self.lords_list_title)

        search = StringVar()
        self.lords_search_entry = Entry(left_frame, textvariable=search)
        self.lords_list = Listbox(left_frame, height=20, width=30,
                                  selectmode=tk.SINGLE)
        self.lords_list.bind('<Button-1>',
                             partial(self.configure_detail_button,
                                     'Lord details', self.lords_details))
        self.lords_search_entry.bind(
            '<Key>', partial(self.input_match_search, search,
                             lambda: self.manager.lords, self.lords_list))

        top_center_frame = Frame(center_frame)
        self.details_button = TkButton(top_center_frame)

        lords_list_label.pack(side=TOP)
        self.lords_search_entry.pack(side=TOP)
        self.lords_list.pack(side=TOP)
        self.details_button.pack(side=TOP)
        top_center_frame.pack(side=TOP)

        locations_list_label = Label(right_frame,
                                     textvariable=self.locations_list_title)
        search = StringVar()
        self.locations_search_entry = Entry(right_frame, textvariable=search)
        self.locations_list = Listbox(right_frame, height=20, width=30,
                                      selectmode=tk.SINGLE)
        self.locations_list.bind(
            '<Button-1>',
            partial(self.configure_detail_button, 'Location details',
                    self.location_details)
            )
        self.locations_search_entry.bind(
            '<Key>', partial(self.input_match_search, search,
                             lambda: self.manager.locations,
                             self.locations_list))

        locations_list_label.pack(side=TOP)
        self.locations_search_entry.pack(side=TOP)
        self.locations_list.pack(side=TOP)

        left_frame.pack(side=LEFT, expand=True, fill=BOTH)
        center_frame.pack(side=LEFT, expand=True, fill=BOTH)
        right_frame.pack(side=LEFT, expand=True, fill=BOTH)

    def update_widgets_values(self):
        """Call this method every time, when user loads or modifies lords database."""
        self.lords_count.set(value=len(self.manager))
        self.lords_female.set(
            value=len(self.manager.get_lords_of_sex(Sex.woman)))
        self.lords_male.set(value=len(self.manager.get_lords_of_sex(Sex.man)))
        self.royalists.set(
            value=len(self.manager.get_lords_by_faction(Faction.royalists)))
        self.nationalists.set(
            value=len(self.manager.get_lords_by_faction(Faction.nationalists)))
        self.neutral.set(
            value=len(self.manager.get_lords_by_faction(Faction.neutral)))
        self.military.set(value=len(
            self.manager.get_lords_of_military_rank()))  # count all officers
        self.clergy.set(value=len(self.manager.get_lords_of_church_title()))
        for title, value in self.lords_by_titles.items():
            value.set(len(self.manager.get_lords_of_title(title)))
        self.locations_count.set(value=len(self.manager.locations))
        for location, value in self.locations_by_type.items():
            value.set(len(self.manager.get_locations_of_type(location)))
        self.update_lords_list()
        self.update_locations_list()

    def change_lords_filter(self, criteria: MyEnum, event: tk.Event):
        text = 'All lords' if criteria is None else f'{plural(criteria.value)}:'
        self.lords_list_title.set(value=text)
        self.lords_filter = criteria
        self.update_lords_list()

    def update_lords_list(self):
        self.lords_list.delete(0, END)
        lords = self.manager.lords
        if isinstance(self.lords_filter, Title):
            lords = self.manager.get_lords_of_title(self.lords_filter)
        elif isinstance(self.lords_filter, Faction):
            lords = self.manager.get_lords_by_faction(self.lords_filter)
        for lord in lords:
            self.lords_list.insert(END, lord.title_and_name)

    def change_locations_filter(self, criteria: MyEnum, event: tk.Event):
        if isinstance(criteria, LocationType):
            self.locations_filter = criteria
        self.update_locations_list()

    def update_locations_list(self):
        self.locations_list.delete(0, END)
        for location in self.manager.get_locations_of_type(
                self.locations_filter):
            self.locations_list.insert(END, location.full_name)

    def load_data(self):
        """Try load Nobleman and Location instances from shelve file."""
        try:
            self.manager.load()
        except error:
            popup = tk.Toplevel(width=400)
            popup.title('Initialization error!')
            tk.Message(popup, text='File lords.sdb was not found!',
                       width=200).pack(fill=BOTH, expand=True)
            TkButton(popup, text='Close', command=popup.destroy).pack(
                side=BOTTOM)
            popup.attributes('-topmost', True)
        else:
            self.update_widgets_values()

    def save_lords(self):
        self.manager.save()

    @staticmethod
    def sdb_file_exists() -> str:
        return NORMAL if os.path.exists('noblemen.sdb') else DISABLED

    def configure_detail_button(self, text: str, function: Callable,
                                event: tk.Event):
        self.details_button.configure(text=text, command=function)

    def lords_details(self):
        instance = self.manager.get_lord_by_name(self.lords_list.get(ACTIVE))
        self.details_window(instance)

    def location_details(self):
        instance = self.manager.get_location_by_name(
            self.locations_list.get(ACTIVE))
        self.details_window(instance)

    def details_window(self, instance: Union[Nobleman, Location]):
        """
        Open new TopLevel window containing detailed data about single Nobleman
        or single Location, which allows to edit the data and save it.
        """
        window = tk.Toplevel()
        window.title(instance.name)
        window.geometry('500x900')
        # filled in step [1] and passed in step [2] to save method when user clicks 'Save ...':
        data: List[Tuple] = []

        for i, name in enumerate(instance.__slots__):
            attr = getattr(instance, name)
            container = tk.Frame(window, relief=tk.GROOVE, borderwidth=1)
            label = self.generate_label(container, name)
            variable, widget = self.generate_data_widget(attr, container, name)
            action = self.generate_action_widget(container, instance, name,
                                                 variable, widget)
            container.pack(side=TOP, expand=True, fill=BOTH)

            data.append((name, attr, widget, variable))  # step 1

        AuthButton(window, text=f'Save {instance.__class__.__name__}',
                   command=lambda: self.save_instance(instance, data)).pack(
            side=TOP)  # step 2

    @staticmethod
    def generate_label(container, name) -> Label:
        label_text = f"{name.replace('_', ' ').lstrip(' ').title()}:"
        return Label(container, text=label_text, bd=1, anchor='w',
                     width=15).pack(side=LEFT, fill=BOTH, expand=False)

    @staticmethod
    def generate_data_widget(attr: Any, container: Frame, name: str) -> Tuple:
        if name in ('portrait', 'image'):
            variable = StringVar(value=single_slashes(attr))
            photo = load_image_or_placeholder(attr)
            widget = Label(container, image=photo, relief=SUNKEN)
            widget.photo = photo
        elif isinstance(attr, str):
            variable = StringVar(value=attr)
            widget = Entry(container, textvariable=variable)
        elif isinstance(attr, int):
            variable = IntVar(value=attr)
            widget = Entry(container,
                           textvariable=variable,
                           width=3 if name == 'age' else 6,
                           justify=CENTER)
        elif isinstance(attr, Tuple):
            variable = x, y = IntVar(value=attr[0]), IntVar(value=attr[1])
            widget = [
                Entry(container, textvariable=x, width=4, justify=CENTER),
                Entry(container, textvariable=y, width=4, justify=CENTER)]
        elif isinstance(attr, MyEnum):
            variable = StringVar(value=attr)
            widget = Spinbox(container, values=[e.value for i, e in
                enumerate(attr.__class__)],
                             textvariable=variable)
            widget.delete(0, END)
            widget.insert(0, attr.value)
        elif isinstance(attr, Set):
            variable = [e.name for e in attr]
            widget = Listbox(container, height=3, selectmode=tk.SINGLE)
            for item in attr:
                widget.insert(END, item.name)
        elif attr is None:
            variable = StringVar(value='')
            widget = Entry(container, textvariable=variable)
        elif isinstance(attr, List):
            variable = StringVar(value='\t'.join(attr))
            widget = Entry(container, textvariable=variable)
        else:  # isinstance(attr, (Nobleman, Location))
            variable = StringVar(value=attr.name)
            widget = Entry(container, textvariable=variable)

        return variable, pack_widget(widget, side=LEFT)

    def generate_action_widget(self, container, instance, name, variable,
                               widget):
        if name in ('portrait', 'image'):
            action = AuthButton(container, text=f'Change {name}',
                                command=partial(self.change_widget_image,
                                                widget, variable))
        elif name == 'full_name':
            action = AuthButton(container, text='Random first_name',
                                command=partial(self.generate_random_name,
                                                variable, instance.sex)
                                )
        elif name in ('_spouse', 'liege'):
            change = AuthButton(container, text='Change',
                                command=partial(self.lords_listbox_window,
                                                instance, name, variable))
            delete = AuthButton(container, text='Delete',
                                command=lambda: variable.set(value=''))
            action = (change, delete)
        elif isinstance(widget, Listbox):
            add = AuthButton(container, text=f'Add {name.lstrip("_")}',
                             command=partial(self.lords_listbox_window,
                                             instance, name, variable, widget))
            delete = AuthButton(container, text='Delete',
                                command=partial(self.clear_list_variable,
                                                variable, widget))
            action = (add, delete)
        else:
            action = None
        return pack_widget(action, side=LEFT,
                           expand=False) if action is not None else None

    def generate_random_name(self, variable: StringVar, sex: Sex):
        variable.set(self.manager.random_lord_name(sex))

    def set_widget_value_to_listbox_value(self, widget: Listbox,
                                          listbox: Listbox, event: tk.Event):
        instance = self.get_listbox_selected_value(event, listbox)
        widget.insert(END, instance.name)

    def set_variable_value_to_listbox_value(self, variable: Any,
                                            listbox: Listbox, event: tk.Event):
        instance = self.get_listbox_selected_value(event, listbox)
        try:
            variable.set(instance.name)
        except AttributeError:
            variable.append(instance.name)

    def get_listbox_selected_value(self, event: tk.Event, listbox: Listbox) -> \
    Union[Nobleman, Location]:
        listbox_selected = listbox.get(f"@{event.x},{event.y}")
        instance = self.manager.get_lord_by_name(listbox_selected)
        return instance

    @staticmethod
    def change_widget_image(widget: Label, variable: StringVar):
        filename = fd.askopenfile(title=f'Select image', mode='r')
        photo = load_image_or_placeholder(filename.name)
        variable.set(filename.name)
        widget.configure(image=photo)
        widget.photo = photo

    def save_instance(self, instance: Union[Nobleman, Location],
                      data: List[Tuple]):
        for tuple_ in data:
            name, attribute, widget, variable = tuple_
            if name in ('portrait', 'image'):
                value = variable.get()
            else:
                value = self.convert_data_to_attribute(name, attribute, widget)
            setattr(instance, name, value)
            if name in ('_spouse', 'liege'):
                other_lord = self.get_object_from_name(value, name)
                setattr(other_lord, name, instance)
        self.manager.add(instance)
        # self.manager.save()  # TODO: uncomment when app is ready
        self.update_widgets_values()

    def convert_data_to_attribute(self, name, attribute, widget) -> Any:
        widget_value = self.get_widget_value(widget)
        if isinstance(attribute, MyEnum):
            return self.cast_value_to_enum(attribute, widget_value)
        elif isinstance(attribute, Set):
            return self.cast_value_to_set(name, widget_value)
        else:
            return widget_value

    def get_widget_value(self, widget):
        """
        Retrieve value of the tkinter widget no matter what
        kind of the widget it is.
        """
        if isinstance(widget, Entry):
            return widget.get()
        elif isinstance(widget, Spinbox):
            widget.selection_element()
            return widget.get()
        elif isinstance(widget, Listbox):
            return widget.get(0, END)
        elif isinstance(widget, List):
            return [self.get_widget_value(w) for w in widget]

    @staticmethod
    def cast_value_to_enum(attribute: Any, widget_value: str):
        """
        Convert string name of the MyEnum retrieved from the tkinter
        widget to the corresponding MyEnum value.
        """
        enum_class: MyEnum = attribute.__class__
        return (t for i, t in enumerate(enum_class)
                if t.value == widget_value).__next__()

    def cast_value_to_set(self, name: str, widget_value: Iterable) -> Set:
        """
        Convert content of list retrieved from Listbox widget to the set
        of corresponding Nobleman or Location instances.
        """
        return set(
            self.get_object_from_name(elem, name) for elem in widget_value)

    def get_object_from_name(self,
                             instance: str,
                             attr_name: str) -> Union[Nobleman, Location]:
        """
        Convert string name of Nobleman or Location instance retrieved
        from the tk.Widget to the instance itself.
        """
        if attr_name in (
        '_children', '_siblings', '_vassals', '_spouse', 'liege'):
            instance = self.manager.get_lord_by_name(instance)
        else:
            instance = self.manager.get_location_by_name(instance)
        return instance

    def lords_listbox_window(self, instance, name: str, variable: Any,
                             widget=None):
        """Display new window with listbox to pick an option."""
        window = tk.Toplevel()
        window.title(f'Pick new {name.lstrip("_")}')
        window.geometry('350x250')

        listbox = AuthListbox(window, width=30)
        if widget is not None:
            listbox.bind('<Button-1>',
                         partial(self.set_widget_value_to_listbox_value,
                                 widget, listbox))
        listbox.bind('<Button-1>',
                     partial(self.set_variable_value_to_listbox_value,
                             variable, listbox), add=True)
        self.fill_listbox_with_data(listbox, instance, name)
        listbox.pack(side=TOP)
        TkButton(window, text='Confirm and close',
                 command=window.destroy).pack(side=TOP)

    def fill_listbox_with_data(self, listbox, instance, name):
        if name in ('_children', '_vassals', '_spouse', '_siblings', 'liege'):
            data = self.get_lords_for_listbox(instance, name)
            [listbox.insert(END, e.title_and_name) for e in data]
        else:
            data = self.get_locations_for_listbox(instance, name)
            [listbox.insert(END, e.name) for e in data]

    def get_lords_for_listbox(self, lord: Nobleman, name: str) -> Union[
        List, Set]:
        if name == '_spouse':
            sex = Sex.man if lord.sex is Sex.woman else Sex.woman  # only opposite sex marriages
            data = self.manager.get_lords_of_sex(sex)
        elif name == 'liege':
            data = [noble for noble in self.manager.lords if
                noble > lord]  # only higher titles
        elif name in ('_siblings', '_children', '_vassals'):
            potential = self.manager.lords
            if name == '_vassals':
                potential = self.manager.get_potential_vassals_for_lord(lord)
            attribute = getattr(lord, name)
            data = potential.difference(attribute)
            if name == '_children':
                data = filter(lambda c: lord.age - c.age > 12, data)
        else:
            data = self.manager.lords
        return data

    def get_locations_for_listbox(self, instance, name):
        return self.manager.locations

    @staticmethod
    def clear_list_variable(list_variable: List, widget: Listbox):
        deleted = widget.get(ACTIVE)
        list_variable.remove(deleted)
        widget.delete(ACTIVE)

    @staticmethod
    def input_match_search(query_variable: StringVar,
                           searched: Callable,
                           updated: Listbox,
                           event: tk.Event):
        """
        Read value of StringVar widget, add character added in this call, and
        match the result with provided Iterable retrieved from call to Callable
        lambda and then update updated Listbox with matching elements.
        """
        if (pressed := event.keysym) == 'BackSpace':
            query = query_variable.get()[:-1]
        elif pressed == 'space':
            query = query_variable.get() + ' '
        else:
            query = query_variable.get() + pressed
        updated.delete(0, END)
        for x in (x.name for x in searched() if query in x.name):
            updated.insert(END, x)


if __name__ == '__main__':
    app = Application()
    app.mainloop()
