from textual.visual import SupportsVisual
from textual.widgets import Static, Switch, Button, TextArea, Label
from textual.containers import Horizontal, Grid
from  daqconf.cider.widgets.configuration_controller import ConfigurationController
from textual.screen import Screen
from os import environ

import json

class DisableObjectToggles(Static):
    def __init__(self, toggleable_config_path: str, content:  str | SupportsVisual = "", *, expand: bool = False, shrink: bool = False, markup: bool = True, name: str | None = None, id: str | None = None, classes: str | None = None, disabled: bool = False) -> None:
        super().__init__(content, expand=expand, shrink=shrink, markup=markup, name=name, id=id, classes=classes, disabled=disabled)
        
        '''
            Config stored in toggleable_config_path contains the following:

                - List of classes of objects we want shifters to be able to see
                - Any attributes we want to find + let them disable
                - <etc.>
        '''
        
        # CHANGE THIS 
        self._config_controller = self.app.get_screen("main").query_one(ConfigurationController)
        self._toggleable_objects = self._read_shifter_config(toggleable_config_path)

        self._session = self._config_controller.get_all_sessions()[0]
    
    def get_session_name(self):
        return getattr(self._session, 'id')
    
    def _read_shifter_config(self, config_path: str):
        # Open config
        with open(config_path, "r") as f:
            full_config = json.load(f)
        
        config = full_config["SwitchOptions"]
        ignored = full_config["IgnoredClasses"]
        
        output_dict = {}
        
        for config_opt in config:
            options = config[config_opt]

            # We need to grab all DALs with that class
            dal_objs = self._config_controller.get_dals_of_class(options["AffectedClasses"])
            
            if options["ApplyToAllDALs"]:
                output_dict[config_opt] = options
                # Get all of them
                options["OutputDal"] = [d for d in dal_objs if d.className() not in ignored]
                continue
            
            for dal in dal_objs:
                if dal.className() in ignored:
                    continue
                
                dal_obj_dict = options.copy()                
                dal_obj_dict["ObjectDal"]=[dal]
                dal_obj_dict["Label"]=f"{dal_obj_dict['Label']} {getattr(dal, 'id')}"

                storage_opt = f"{getattr(dal, 'id')}_{config_opt}"
                
                output_dict[storage_opt] = dal_obj_dict
            
        return output_dict                


    def generate_switch(self, object_name: str, switch_label: str, is_switched_on: bool):
        return Horizontal(
            Static(f"{switch_label}:                  ",  classes="label"),
            Switch(animate=False, id=object_name, value=is_switched_on),
            classes="container"
        )
    
    def compose(self):
        # Firstly we need components
        # for dal in self._toggleable_attributes:
        for object_names, object_options in self._toggleable_objects.items():
            yield self.generate_switch(object_names, object_options["Label"], True)
        
        yield Button(label="Save Config", id="save_cfg", variant="success")

    def on_switch_changed(self, event: Switch.Changed):
        if self._toggleable_objects.get(event.switch.id, None) is None:
            return
        
        if self._toggleable_objects.get(event.switch.id)['AttributeName'] == 'disabled':
            self._config_controller.current_dal = self._toggleable_objects.get(event.switch.id)['ObjectDal'][0]
            self._config_controller.toggle_disable_conf_obj_in_session(self._session, event.switch.value)
        
        # For now we assume must be boolean
        else:
            for dal in self._toggleable_objects.get(event.switch.id)['ObjectDal']:
                self._config_controller.current_dal = dal

                self._config_controller.update_configuration(self._toggleable_objects.get(event.switch.id)['AttributeName'], 
                                                             event.switch.value)
                
    async def on_button_pressed(self, _: Button.Pressed):
        self._config_controller.commit_configuration("Finish enable/disable")
        message = f"drunc-unified-shell ssh-standalone {self._config_controller.get_config_file_name()} {getattr(self._session, 'id')}"
        
        self.app.push_screen(ExitScreen(message))


class ExitScreen(Screen):
    """Screen with a dialog to quit."""
    css_file_path = f"{environ.get('DAQCONF_SHARE')}/config/textual_dbe/textual_css"

    CSS_PATH = f"{css_file_path}/quit_screen.tcss"

    def __init__(self, message: str, name: str | None = None, id: str | None = None, classes: str | None = None) -> None:        
        super().__init__(name, id, classes)
        self._message = message

    def compose(self):
        yield Grid(
            Label(f"Please copy/paste {self._message}", id="question"),
            # Button("Copy Command", variant="success", id="copy"),
            Button("Quit", variant="error", id="quit"),
            Button("Cancel", variant="warning", id="cancel"),

            id="dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "quit":
            self.app.exit(self._message)
        # elif event.button.id == "copy":
        #     # pyperclip.copy(self._message)
        #     self.app.exit()
        else:
            self.app.pop_screen()
