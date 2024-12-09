
from typing import Dict

from textual.widgets import Input, Button, Static
from textual.containers import Horizontal, Container

from daqconf.cider.widgets.configuration_controller import ConfigurationController

class __MenuWithButtons(Static):
    def __init__(self, button_labels: Dict[str, Dict[str, str]], input_message: str="", name: str | None=None, id: str | None = None, classes: str | None = None) -> None:
        super().__init__(name=name, id=id, classes=classes)
        """Base class for popups with N buttons and a single input field
        """        

        self._button_labels = button_labels
        self._main_screen = self.app.get_screen("main")
        self._config_controller = self._main_screen.query_one(ConfigurationController)
        self._input_message = input_message

    def compose(self):
        """Generates interfaxce
        """
        with Container(id="save_box"):
            yield Input(placeholder=self._input_message, classes="save_message")
            with Horizontal(classes="buttons"):
                # Add buttons
                for button_text, button_properties in self._button_labels.items():
                    yield Button(button_properties["label"], id=button_text, variant=button_properties["variant"])
                yield Button("Cancel", id="cancel", variant="error")
            # Add input field
        
    def button_actions(self, button_id: str| None):
        raise NotImplementedError("button_actions should be implemented in the child class")
        
    def input_action(self, message: str):
        raise NotImplementedError("input_action should be implemented in the child class")
            
    def on_input_submitted(self, event):
        if event.value:        
            self.input_action(event.value)
            self.app.screen.dismiss(result="yay")
        
    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id != "cancel":
            self.button_actions(event.button.id)
        
        # Cancel button does this too but no need to check!
        self.app.screen.dismiss(result="yay")
        
####### File Saving ##########

class SaveWithMessage(__MenuWithButtons):
    def __init__(self, name: str | None = None, id: str | None = None, classes: str | None = None) -> None:
        """
        Concrete class for saving configuration with a message
        """
        self._button_labels = {
            "save" : {"label": "Save", "variant": "success"}
        }
        
        super().__init__(self._button_labels, "Enter update message", name, id, classes)

    def input_action(self, message: str):
        self._config_controller.commit_configuration(message)
    
    def button_actions(self, button_id: str):
        match button_id:
            case "save":
                input = self.query_one(Input)
                self.input_action(input.value)
            case _:
                return         
        
####### File Opening ##########
class OpenFile(__MenuWithButtons):
    def __init__(self, name: str | None = None, id: str | None = None, classes: str | None = None) -> None:
        
        self._button_labels = {
            "open" : {"label": "Open", "variant": "success"},
            "browse" : {"label": "Browse [DOESN'T WORK]", "variant": "warning"}
        }
        """
        Concrete class for opening a configuration file
        """
        
        super().__init__(self._button_labels, "Enter file path", name, id, classes)


    def input_action(self, new_config: str):
        """
        Add new handler based on config name
        """
        try:
            self._main_screen.update_with_new_input(new_config)        
        except Exception as e:
            logger = self._main_screen.query_one("RichLogWError")
            logger.write_error(e)
    
    def button_actions(self, button_id: str | None):
        """Open file or browse for file (not implemented)

        Arguments:
            button_id -- Button label
        """        
        match button_id:
            case "open":
                input = self.query_one(Input)
                
                # Safety check to avoid empty input
                if input:                
                    self.input_action(input.value)

            case "browse":
                logger = self._main_screen.query_one("RichLogWError")
                logger.write_error("Sorry not done this yet, please enter full file path and hit enter/open!")
            case _:
                return


######## Rename Object ###########
class RenameConfigObject(__MenuWithButtons):
    def __init__(self, name: str | None = None, id: str | None = None, classes: str | None = None) -> None:
        
        self._button_labels = {
            "rename" : {"label": "Rename", "variant": "success"}
        }
        """
        Concrete class for opening a configuration file
        """
        
        super().__init__(self._button_labels, "", name, id, classes)

        # Bit hacky but "shrug"
        self._input_message = getattr(self._config_controller.current_dal, "id")

        
    def input_action(self, new_file_name: str):
        """
        Add new handler based on config name
        """
        try:
            self._config_controller.rename_dal(new_file_name) 
            main_screen = self.app.get_screen("main")
            selection_menu = main_screen.query_exactly_one("SelectionPanel")
            selection_menu.refresh(recompose=True)
            selection_menu.restore_menu_state()

        except Exception as e:
            logger = self._main_screen.query_one("RichLogWError")
            logger.write_error(e)
    
    def button_actions(self, button_id: str | None):
        """Open file or browse for file (not implemented)

        Arguments:
            button_id -- Button label
        """        
        match button_id:
            case "rename":
                input = self.query_one(Input)
                
                # Safety check to avoid empty input
                if input:                
                    self.input_action(input.value)

            case _:
                return

