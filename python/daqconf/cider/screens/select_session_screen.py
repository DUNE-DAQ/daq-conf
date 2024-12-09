from daqconf.cider.widgets.select_session import SelectSession


from textual.screen import ModalScreen


from os import environ


class SelectSessionScreen(ModalScreen):
    css_file_path = f"{environ.get('DAQCONF_SHARE')}/config/textual_dbe/textual_css"
    CSS_PATH = f"{css_file_path}/session_selection_layout.tcss"

    def compose(self):
        yield SelectSession()

    def on_mount(self)->None:
        self.query_one(SelectSession).focus()