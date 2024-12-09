'''
App for testing configuration 
'''
from os import environ
from daqconf.cider.screens.cider_main_screen import CiderMainScreen

# Textual Imports
from textual.app import App

class Cider(App):
    # HACK: Need to sort this, only way to get the CSS to work
    css_file_path = f"{environ.get('DAQCONF_SHARE')}/config/textual_dbe/textual_css"

    CSS_PATH = f"{css_file_path}/main_app_layout.tcss"
    SCREENS = {"main": CiderMainScreen}
    
    _input_file_name = None
    
    def set_input_file(self, input_file_name: str):
        self._input_file_name = input_file_name
    
    def on_mount(self):
        
        self.push_screen("main")
        if self._input_file_name is not None:
            self.app.get_screen("main").set_initial_input_file(self._input_file_name)
