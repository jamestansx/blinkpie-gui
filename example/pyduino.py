import kivy
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.network.urlrequest import UrlRequest
from kivy.clock import Clock
from kivy.storage.jsonstore import JsonStore

kivy.require("2.0.0")
store = JsonStore("settings.json")


class SetupScreen(Screen):
    def __init__(self, **kwargs):
        super(SetupScreen, self).__init__(**kwargs)

    def setting(self):
        if not store.exists("iplink"):
            store.put("iplink", link=self.ids.ip_input.text)


class MainScreen(Screen):

    gettext = StringProperty("")
    server = ""

    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        Clock.schedule_interval(self.do_get, 0.5)

    def do_get(self, dt):
        if store.exists("iplink"):
            self.server = "https://" + store.get("iplink")["link"] + ":443"
        req = UrlRequest(
            self.server, verify=False, debug=True
        )
        self.gettext = req.req_body

    def do_post(self):
        req = UrlRequest(
            self.server,
            verify=False,
            req_body=str(self.ids.post_text.text),
            debug=True,
        )

    def on_success(self, req, result):
        self.gettext = result


class PyduinoApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(SetupScreen(name="setup"))
        sm.add_widget(MainScreen(name="main"))
        store = JsonStore("settings.json")
        if store.exists("iplink"):
            sm.current = "main"
        return sm


if __name__ == "__main__":
    PyduinoApp().run()
