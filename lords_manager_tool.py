#!/usr/bin/env python

import os
import string
import shelve
import tkinter as tk
import tkinter.filedialog as fd

from dbm import error
from functools import partial
from typing import Any, Iterable, Tuple, Callable, Generator
from tkinter import (
    DISABLED, NORMAL, BOTH, TOP, LEFT, RIGHT, BOTTOM, CENTER, END, IntVar,
    StringVar, Label, Entry, Spinbox, Listbox, Frame, LabelFrame, ACTIVE,
    SUNKEN, Button as TkButton
)
from functions import (load_image_or_placeholder, plural, localize,
    input_match_search, get_current_language, slot_to_field
)
from classes import *
from lords_manager import LordsManager

WINDOW_TITLE = 'Lords Manager'
LORDS_SETS = ('_children', '_vassals', '_spouse', '_siblings', 'liege')


def pack_widget(widget, **kwargs):
    """Pack widgets and nested widgets recursively."""
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

    def __init__(self, language: str):
        super().__init__()
        self.wm_title(WINDOW_TITLE)

        self.language = language
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

        # Handles to retrieve additional TopLevel windows opened by user. We
        # keep two dicts of windows for Noblemen and Location instances,
        # and each window is identified by it's instance id integer key:
        self.extra_windows = {Nobleman: {}, Location: {}}
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
            text = plural(title.value, self.language)
            label = Label(section, text=f'{text.title()}:')
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
            text = plural(location.value, self.language)
            label = Label(section, text=f'{text.title()}:')
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

        AuthButton(section,
                   command=partial(self.new_instance_and_window, Nobleman),
                   text='Add new lord',
                   state=self.sdb_file_exists()).pack(side=LEFT)

        TkButton(section, command=self.load_data, text='Reload data',
                 state=self.sdb_file_exists()).pack(side=LEFT, padx=380)

        AuthButton(section,
                   command=partial(self.new_instance_and_window, Location),
                   text='Add new location',
                   state=self.sdb_file_exists()).pack(side=RIGHT)

    def create_lords_and_fiefs_section(self):
        """
        In this section two lists re displayed: Lords on the left and Locations on the right
        side of the window. In the middle a picture of currently selected object and button
        opening detail-view is displayed.
        """
        section = self.sections['Lords and fiefs:']
        self.lords_searching_list(section)
        self.details_section(section)
        self.locations_searching_list(section)

    def lords_searching_list(self, section):
        left_frame = Frame(section)
        lords_list_label = Label(left_frame,
                                 textvariable=self.lords_list_title)
        variable = StringVar()
        self.lords_search_entry = Entry(left_frame, textvariable=variable)
        self.lords_list = Listbox(left_frame, height=20, width=35,
                                  selectmode=tk.SINGLE)
        self.lords_list.bind('<Button-1>',
                             partial(self.configure_detail_button,
                                     'Lord details',
                                     self.lords_details))
        self.lords_search_entry.bind(
            '<Key>', partial(input_match_search, variable,
                             lambda: self.manager.lords, self.lords_list))
        lords_list_label.pack(side=TOP)
        self.lords_search_entry.pack(side=TOP)
        self.lords_list.pack(side=TOP)
        left_frame.pack(side=LEFT, expand=True, fill=BOTH)

    def details_section(self, section):
        center_frame = Frame(section)
        top_center_frame = Frame(center_frame)
        self.details_button = TkButton(top_center_frame)
        self.selected_image = Label(top_center_frame)
        self.details_button.pack(side=TOP)
        self.selected_image.pack(side=TOP)
        top_center_frame.pack(side=TOP)
        center_frame.pack(side=LEFT, expand=True, fill=BOTH)

    def locations_searching_list(self, section):
        right_frame = Frame(section)
        locations_list_label = Label(right_frame,
                                     textvariable=self.locations_list_title)
        variable = StringVar()
        self.locations_search_entry = Entry(right_frame, textvariable=variable)
        self.locations_list = Listbox(right_frame, height=20, width=35,
                                      selectmode=tk.SINGLE)
        args = 'Location details', self.location_details
        self.locations_list.bind(
            '<Button-1>', partial(self.configure_detail_button, *args))
        self.locations_search_entry.bind(
            '<Key>', partial(input_match_search, variable,
                             lambda: self.manager.locations,
                             self.locations_list))
        locations_list_label.pack(side=TOP)
        self.locations_search_entry.pack(side=TOP)
        self.locations_list.pack(side=TOP)
        right_frame.pack(side=LEFT, expand=True, fill=BOTH)

    def update_widgets_values(self):
        """
        Call this method every time, when user loads or modifies lords
        database.
        """
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
        self.locations_count.set(value=len(self.manager._locations))
        for location, value in self.locations_by_type.items():
            value.set(len(self.manager.get_locations_of_type(location)))
        self.update_lords_list()
        self.update_locations_list()

    def change_lords_filter(self, criteria: MyEnum, event: tk.Event):
        if criteria is None:
            text = localize('All lords', self.language)
        else:
            text = f'{plural(criteria.value, self.language)}:'
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
        """
        Set the correct callback for the detail_button according to the curently
        active Listbox in main window. Button could open Nobleman-editing window
        or Location-editing window.
        """
        self.details_button.configure(text=text,
                                      command=partial(function, event))

    def lords_details(self, event: tk.Event):
        name = self.get_instance_name(event)
        instance = self.manager.get_lord_by_name(name)
        self.open_new_or_show_opened_window(instance)

    def location_details(self, event: tk.Event):
        name = self.get_instance_name(event)
        instance = self.manager.get_location_by_name(name)
        self.open_new_or_show_opened_window(instance)

    @staticmethod
    def get_instance_name(event: tk.Event) -> str:
        if isinstance(widget := event.widget, Listbox):
            name = widget.get(ACTIVE)
        else:  # Entry widget
            name = widget.get()
        return name

    def open_new_or_show_opened_window(self, instance):
        if window := self.window_for_instance_already_opened(instance):
            window.lift()
        else:
            self.manager.convert_ids_to_instances(instance)
            self.details_window(instance)

    def window_for_instance_already_opened(self, instance) -> Optional[
        tk.Toplevel]:
        try:
            return self.extra_windows[type(instance)][instance.id]
        except KeyError:
            return

    def new_instance_and_window(self, object_type: Union[
        type(Nobleman), type(Location)]):
        if object_type is Nobleman:
            instance = Nobleman(len(self.manager.lords), 'ADD NAME',
                                nationality=Nationality.choice())
        else:
            instance = Location(len(self.manager.locations), 'ADD NAME')
        self.details_window(instance)

    def details_window(self, instance: Union[Nobleman, Location]):
        """
        Open new TopLevel window containing detailed data about single Nobleman
        or single Location, which allows to edit the data and save it.
        """
        window = tk.Toplevel()
        window.geometry('625x900')
        window.title(instance.name)
        window.protocol("WM_DELETE_WINDOW",
                        partial(self.close_details_window, instance))
        self.register_extra_window(instance, window)
        self.generate_window_content(instance, window)

    def generate_window_content(self,
                                instance: Union[Nobleman, Location],
                                window: tk.Toplevel):
        # filled in step [1] and passed in step [2] to save method when user
        # clicks 'Save ...':
        data: List[Tuple] = []
        no_widgets = ('id', 'map_icon')
        for name in (n for n in instance.__slots__ if n not in no_widgets):
            attr = getattr(instance, name)
            container = tk.Frame(window, relief=tk.GROOVE, borderwidth=1)
            label = self.generate_label(container, name)
            variable, widget = self.generate_data_widget(attr, container, name)
            action = self.generate_action_widget(container, instance, name,
                                                 variable, widget)
            container.pack(side=TOP, expand=True, fill=BOTH)

            data.append((name, attr, variable, widget))  # step 1

        AuthButton(window, text=f'Save {instance.__class__.__name__}',
                   command=lambda: self.save_instance(instance, data)).pack(
            side=TOP)  # step 2

    def register_extra_window(self,
                              instance: Union[Nobleman, Location],
                              window: tk.Toplevel):
        """
        Add new window reference to the self.extra_windows nested dict to allow
        keeping track of opened additional windows, update their contents etc.
        """
        self.extra_windows[instance.__class__][instance.id] = window

    def unregister_extra_window(self, instance: Union[Nobleman, Location]):
        self.extra_windows[instance.__class__][instance.id].destroy()
        del self.extra_windows[instance.__class__][instance.id]

    def close_details_window(self, instance: Union[Nobleman, Location]):
        """
        Close window and converts edited data to lightweight formats to make
        saved database shelve file small and quick-open-able.
        """
        self.manager.prepare_for_save(instance)
        self.unregister_extra_window(instance)

    @staticmethod
    def generate_label(container, name) -> Label:
        label_text = slot_to_field(name)
        return Label(container, text=label_text, bd=1, anchor='w',
                     width=15).pack(side=LEFT, fill=BOTH, expand=False)

    def generate_data_widget(self,
                             attr: Any,
                             container: Frame,
                             name: str) -> Tuple:
        data = attr, container
        if isinstance(attr, str):
            variable, widget = self.widget_from_string_attribute(*data, name)
        elif isinstance(attr, int):
            variable, widget = self.widget_from_int_attribute(*data, name)
        elif isinstance(attr, Tuple):
            variable, widget = self.widget_from_int_tuple(*data)
        elif isinstance(attr, MyEnum):
            variable, widget = self.widget_from_enum_attribute(*data)
        elif isinstance(attr, Set):
            variable, widget = self.widget_from_set_attribute(*data, name)
        elif isinstance(attr, List):
            variable, widget = self.widget_from_list_attribute(*data)
        else:  # isinstance(attr, (Nobleman, Location)):
            variable, widget = self.widget_from_instance_or_none(*data)
        return variable, pack_widget(widget, side=LEFT)

    @staticmethod
    def widget_from_string_attribute(attr: str, container, name):
        variable = StringVar(value=attr)
        if name in ('portrait', 'image', 'picture'):
            photo = load_image_or_placeholder(attr)
            widget = Label(container, image=photo, relief=SUNKEN)
            widget.photo = photo
        else:
            widget = Entry(container, textvariable=variable, width=35)
        return variable, widget

    @staticmethod
    def widget_from_int_attribute(attr, container, name):
        variable = IntVar(value=attr)
        widget = Entry(container,
                       textvariable=variable,
                       width=3 if name == 'age' else 6,
                       justify=CENTER)
        return variable, widget

    @staticmethod
    def widget_from_int_tuple(attr, container):
        variable = x, y = IntVar(value=attr[0]), IntVar(value=attr[1])
        widget = [
            Entry(container, textvariable=x, width=5, justify=CENTER),
            Entry(container, textvariable=y, width=5, justify=CENTER)]
        return variable, widget

    def widget_from_set_attribute(self, attr, container, name: str):
        variable = [e.name for e in attr]
        widget = Listbox(container, height=3, width=35,selectmode=tk.SINGLE)
        func = self.lords_details if name in LORDS_SETS else self.location_details
        widget.bind('<Double-Button-1>', func)
        for item in attr:
            widget.insert(END, item.name)
        return variable, widget

    @staticmethod
    def widget_from_enum_attribute(attr, container):
        variable = StringVar(value=attr)
        widget = Spinbox(container,
                         values=[e.value for i, e in
                                 enumerate(attr.__class__)],
                         textvariable=variable)
        widget.delete(0, END)
        widget.insert(0, attr.value)
        return variable, widget

    @staticmethod
    def widget_from_list_attribute(attr, container):
        variable = StringVar(value='\t'.join(attr))
        widget = Entry(container, textvariable=variable)
        return variable, widget

    def widget_from_instance_or_none(self, attr, container):
        variable = StringVar(value='' if attr is None else attr.name)
        widget = Entry(container, textvariable=variable, width=35)
        widget.bind('<Double-Button-1>', self.lords_details)
        return variable, widget

    def generate_action_widget(self, container, instance, name, variable,
                               widget):
        """
        Create proper interactive widget: Button or other object which user
        can interact with to manipulate data of the data widget provided.
        """
        if name in ('portrait', 'image', 'picture'):
            action = self.image_action_widget(container, name, variable, widget)
        elif name == 'full_name':
            action = self.new_name_action_widget(container, instance, variable)
        elif name in ('_spouse', 'liege'):
            action = self.pick_lord_action(container, instance, name, variable)
        elif isinstance(widget, Listbox):
            action = self.listbox_action_widget(container, instance, name,
                                                variable, widget)
        else:
            return None
        return pack_widget(action, side=LEFT, fill='x', expand=True)

    def new_name_action_widget(self, container, instance, variable):
        return AuthButton(
            container, text='Random name', command=partial(
                self.generate_random_name, variable, instance.sex))

    def image_action_widget(self, container, name, variable, widget):
        return AuthButton(
            container, text=f'Change {name}', command=partial(
                self.change_widget_image, widget, variable))

    def pick_lord_action(self, container, instance, name, variable):
        if name == '_spouse':
            change_text, delete_text = 'New marriage', 'Divorce'
        else:
            change_text, delete_text = 'New liege', 'Break feudal bond'
        return (
            AuthButton(container, text=change_text,
                       command=partial(self.lords_listbox_window, instance,
                                       name, variable)),
            AuthButton(container, text=delete_text,
                       command=lambda: variable.set(value=''))
        )

    def listbox_action_widget(self, container, instance, name, variable,
                              widget):
        add = AuthButton(container, text=f'Add {name.lstrip("_")}',
                         command=partial(self.lords_listbox_window,
                                         instance, name, variable, widget))
        delete = AuthButton(container, text='Delete',
                            command=partial(self.clear_list_variable,
                                            variable, widget))
        return (add, delete)

    def generate_random_name(self, variable: StringVar, sex: Sex):
        variable.set(self.manager.random_lord_name(sex))

    @staticmethod
    def set_widget_value_to_listbox_value(widget: Listbox,
                                          listbox: Listbox, event: tk.Event):
        name = listbox.get(f"@{event.x},{event.y}")
        widget.insert(END, name)

    @staticmethod
    def set_variable_value_to_listbox_value(variable: Any,
                                            listbox: Listbox, event: tk.Event):
        name = listbox.get(f"@{event.x},{event.y}")
        try:
            variable.set(name)
        except AttributeError:
            variable.append(name)

    def get_listbox_selected_value(self,
                                   event: tk.Event,
                                   listbox: Listbox) -> Union[
        Nobleman, Location]:
        listbox_selected = listbox.get(f"@{event.x},{event.y}")
        try:
            instance = self.manager.get_lord_by_name(listbox_selected)
        except StopIteration:
            instance = self.manager.get_location_by_name(listbox_selected)
        return instance

    @staticmethod
    def change_widget_image(widget: Label, variable: StringVar):
        filename = fd.askopenfile(title=f'Select image', mode='r')
        photo = load_image_or_placeholder(filename.name)
        variable.set(filename.name)
        widget.configure(image=photo)
        widget.photo = photo

    def save_instance(self,
                      instance: Union[Nobleman, Location],
                      data: List[Tuple]):
        for tuple_ in data:
            self.save_single_attribute(instance, tuple_)
        self.close_details_window(instance)
        self.manager.add(instance)
        self.manager.save()  # TODO: uncomment when app is ready
        self.refresh_windows()

    def refresh_windows(self):
        """
        When object data in one extra-window is changed and saved, update
        data in all other extra-windows currently opened.
        """
        print(self.extra_windows)
        for window_class, windows in self.extra_windows.items():
            obj = 'lord' if window_class is Nobleman else 'location'
            func = eval(f'self.manager.get_{obj}_of_id')
            for id, window in windows.items():
                instance = func(id)
                self.destroy_children_widgets(window)
                self.generate_window_content(instance, window)
        self.update_widgets_values()

    @staticmethod
    def destroy_children_widgets(window):
        for widget in window.winfo_children():
            widget.destroy()

    def save_single_attribute(self,
                              instance: Union[Nobleman, Location],
                              tuple_: Tuple):
        name, attribute, variable, widget = tuple_
        if name in ('portrait', 'image'):
            value = variable.get()
        else:
            value = self.convert_data_to_attribute(name, attribute, widget)
        setattr(instance, name, value)

    def convert_data_to_attribute(self, name, attribute, widget) -> Any:
        value = self.get_widget_value(widget)
        if isinstance(attribute, MyEnum):
            return self.cast_value_to_enum(attribute, value)
        elif isinstance(attribute, Set):
            return self.cast_value_to_set(name, value)
        elif isinstance(attribute, int):
            return int(value)
        elif isinstance(attribute, str):
            return value
        elif isinstance(attribute, Tuple):
            entry_x, entry_y = widget  # data from two Entry widgets in list
            return int(entry_x.get()), int(entry_y.get())
        else:
            return self.get_object_from_name(value, name)

    def get_widget_value(self, widget):
        """
        Retrieve value of the tkinter widget no matter what kind of the widget
        it is. Return raw, unprocessed value for further processing.
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
        Convert string name of the MyEnum retrieved from the tkinter widget
        to the corresponding MyEnum value.
        """
        enum_class: MyEnum = attribute.__class__
        return (t for i, t in enumerate(enum_class)
                if t.value == widget_value).__next__()

    def cast_value_to_set(self, name: str, value: Iterable) -> Set:
        """
        Convert content of list retrieved from Listbox widget to the set
        of corresponding Nobleman or Location instances.
        """
        return set(self.get_object_from_name(elem, name) for elem in value)

    def get_object_from_name(self,
                             value: str,
                             attr_name: str) -> Union[Nobleman, Location, str]:
        """
        Cast widget value to correct type for attribute name.
        """
        if not value:  # empty Entry and StringVar contains empty string
            return value
        elif attr_name in LORDS_SETS:
            return self.manager.get_lord_by_name(value)
        elif attr_name == '_fiefs':
            return self.manager.get_location_by_name(value)

    def lords_listbox_window(self,
                             instance: Nobleman,
                             name: str,
                             variable: Any,
                             widget=None):
        """Display new window with listbox to pick an option."""
        window = tk.Toplevel()
        window.title(f'Pick new {name.lstrip("_")}')
        window.geometry('350x250')

        listbox = self.create_lords_listbox(variable, widget, window)
        for name in self.get_data_for_listbox(instance, name):
            listbox.insert(END, name)

        TkButton(window, text='Confirm and close',
                 command=window.destroy).pack(side=TOP)

    def create_lords_listbox(self, variable, widget, window):
        listbox = AuthListbox(window, width=30)
        listbox.bind('<Button-1>',
                     partial(self.set_variable_value_to_listbox_value,
                             variable, listbox), add=True)
        if widget is not None:
            listbox.bind('<Button-1>',
                         partial(self.set_widget_value_to_listbox_value,
                                 widget, listbox))
        return pack_widget(listbox, side=TOP)

    def get_data_for_listbox(self,
                             instance: Union[Nobleman, Location],
                             name: str) -> Generator:
        if name in LORDS_SETS:
            data = self.get_lords_for_listbox(instance, name)
        else:
            data = self.get_locations_for_listbox(instance, name)
        return (e.name for e in data)

    def get_lords_for_listbox(self, lord: Nobleman, name: str) -> Set:
        if name == '_spouse':
            data = self.get_potential_spouses(lord)
        elif name == 'liege':
            data = {noble for noble in self.manager.lords if noble > lord}
        elif name in ('_siblings', '_children', '_vassals'):
            data = self.get_potential_kins_or_vassals(lord, name)
        else:
            return self.manager.lords
        return data

    def get_potential_spouses(self, lord: Nobleman) -> Iterable:
        sex = Sex.man if lord.sex is Sex.woman else Sex.woman
        return filter(lambda s: not s.spouse, self.manager.get_lords_of_sex(sex))

    def get_potential_kins_or_vassals(self, lord: Nobleman, name: str) -> Iterable:
        potential = self.manager.lords
        if name == '_vassals':
            potential = self.manager.get_potential_vassals_for_lord(lord)
        elif name == '_children':
            potential = filter(lambda c: lord.age - c.age > 12, potential)
        return set(potential)

    def get_locations_for_listbox(self, instance: Location, name: str):
        return self.manager.locations

    @staticmethod
    def clear_list_variable(list_variable: List, widget: Listbox):
        deleted = widget.get(ACTIVE)
        try:
            list_variable.remove(deleted)
        except ValueError:
            pass
        finally:
            widget.delete(ACTIVE)


if __name__ == '__main__':
    language = get_current_language()
    app = Application(language)
    app.mainloop()
