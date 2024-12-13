from textual.widgets import Button, Label
from textual.screen import Screen
from textual.containers import Grid
from textual.app import ComposeResult
from os import environ

from daqconf.cider.widgets.disable_object_toggles import DisableObjectToggles

class DisableObjectToggleScreen(Screen):
    CONFIG_FILE_FOLDER = f"{environ.get('DAQCONF_SHARE')}/config/textual_dbe/shifter_config"
    CONFIG_FILE_PATH = f"{CONFIG_FILE_FOLDER}/dummy_config.json"
    
    css_file_path = f"{environ.get('DAQCONF_SHARE')}/config/textual_dbe/textual_css"

    CSS_PATH = f"{css_file_path}/toggle_screen.tcss"

    

    def compose(self):
        yield DisableObjectToggles(self.CONFIG_FILE_PATH)
        