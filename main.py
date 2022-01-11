import kivy

kivy.require("2.0.0")

from uuid import uuid4

from kivy.app import App
from kivy.clock import Clock
from kivy.properties import ListProperty, ObjectProperty, StringProperty, NumericProperty
from kivy.storage.jsonstore import JsonStore
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from kivy.uix.textinput import TextInput
from requests import get, post

db = JsonStore("db.json")

project_title = ObjectProperty(None)


def get_servername() -> str:
    if db.exists("ip_address"):
        server = "https://" + db.get("ip_address")["link"] + ":443"
    else:
        SetupIpWidget().open()
    return server


class AuthError(Popup):
    ...


class SetupIpWidget(Popup):
    def on_dismiss(self):
        db.put("ip_address", link=self.ids.ip_input.text)
        return super().on_dismiss()


class MenuScreen(Screen):
    def __init__(self, **kwargs):
        super(MenuScreen, self).__init__(**kwargs)
        Clock.schedule_once(self.setup_ip, 2)

    def setup_ip(self, dt):
        if not db.exists("ip_address"):
            show = SetupIpWidget()
            show.open()


class NewProjectScreen(Screen):

    uuid_value = StringProperty("")

    def __init__(self, **kwargs):
        super(NewProjectScreen, self).__init__(**kwargs)

    def genUUID(self):
        self.uuid_value = uuid4().hex

    def create_project(self):
        data = {
            "profile": {
                "UUID": self.ids.UUID.text,
                "name": self.ids.project_title.text,
                "description": self.ids.description.text,
            }
        }
        posts = post(get_servername(), verify=False, json=data)
        if posts.status_code != 200:
            ...
        db.put(
            self.ids.project_title.text,
            UUID=self.ids.UUID.text,
            name=self.ids.device_name.text,
            description=self.ids.description.text,
        )
        global project_title
        project_title = self.ids.project_title.text


class ProjectList(DropDown):
    UUID = StringProperty()
    device_name = StringProperty()
    description = StringProperty()

    def __init__(self, **kwargs):
        super(ProjectList, self).__init__(**kwargs)
        self.keys = db.keys()
        self.project_list()

    def project_list(self):
        keys = self.keys
        keys.remove("ip_address")
        if not keys:
            lbl = Label(
                text="No project available",
                size_hint_y=None,
                height=44,
                color=(88, 88, 88),
            )
            self.add_widget(lbl)
        else:
            for i in keys:
                if "ip_address" != i:
                    btn = Button(text=i, size_hint_y=None, height=44)
                    btn.bind(on_release=self.add_project_detail)
                    self.add_widget(btn)

    def add_project_detail(self, btn):
        key = btn.text
        self.select(key)
        projects = dict()
        for i in self.keys:
            if i != "ip_address":
                projects[i] = db.get(i)
        App.get_running_app().root.ids.selectproject_screen.ids.UUID.text = (
            projects[key]["UUID"]
        )
        App.get_running_app().root.ids.selectproject_screen.ids.device_name.text = projects[
            key
        ][
            "name"
        ]
        App.get_running_app().root.ids.selectproject_screen.ids.description.text = projects[
            key
        ][
            "description"
        ]

    def open_project(self, bt):
        global project_title
        choice = (
            App.get_running_app().root.ids.selectproject_screen.ids.mainbutton.text
        )
        if choice not in ["Projects", ""]:
            project_title = choice
            App.get_running_app().root.current = "main_screen"


class SelectProjectScreen(Screen):
    def __init__(self, **kwargs):
        super(SelectProjectScreen, self).__init__(**kwargs)


class MainScreen(Screen):
    project = StringProperty()
    server = StringProperty()
    request_types = ["data", "notification", "profile"]
    request = ["temp", "rain", "led", "windows", "ledr"]
    get_data = ListProperty(["" for _ in request])

    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)

    def on_pre_enter(self):
        self.project = str(project_title)
        self.server = get_servername()
        Clock.schedule_once(self._do_auth, 0.1)
        Clock.schedule_interval(self._do_get, 3)

    def _do_get(self, dt):
        for i, n in enumerate(self.request):
            isbool = False
            en = False
            params = {self.request_types[0]: n}
            gets = get(self.server, verify=False, params=params)
            if n in ["rain", "led", "ledr"]:
                en = True
            if n == "rain":
                isbool = True
            if gets.status_code == 200:
                self.get_data[i] = self._parse_data(gets.text, isbool, en)

    def _parse_data(self, value: str, isbool: True, en:bool):
        if not en:
            return value
        if isbool:
            STAT = [True, False]
        else:
            STAT = ["OFF", "ON"]

        if int(float(value)) == 1 or int(float(value)) == 0:
            return STAT[int(float(value))]
        else:
            return value

    def _do_post(self, method, id, value):
        data = {method: {id: value}}
        print(data)
        posts = post(self.server, verify=False, json=data)

    def _do_auth(self, dt):
        param = {self.request_types[2]: db.get(project_title)["UUID"]}
        gets = get(self.server, verify=False, params=param)
        if gets.status_code != 200:
            error = AuthError()
            error.message.text = (
                "Failed to authenticate! Please recreate the project..."
            )
            error.open()

    def switch_call(self, instance, value):
        self._do_post("data", "ledr", str(int(value)))
        a = self._parse_data(str(int(value)), False, True)
        self.get_data[4] = a


class BlinkpieApp(App):
    def build(self):
        ...


if __name__ == "__main__":
    BlinkpieApp().run()
