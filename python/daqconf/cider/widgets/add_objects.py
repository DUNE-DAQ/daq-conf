
from textual.widgets import Static, Input, Select, Button
from textual.containers import Container, Horizontal

from daqconf.cider.widgets.configuration_controller import ConfigurationController
from daqconf.cider.widgets.custom_rich_log import RichLogWError

class AddNewObject(Static):
    def compose(self):
        # Standard copy/paste
        self._main_screen = self.app.get_screen("main")
        self._config_controller: ConfigurationController = self._main_screen.query_one(ConfigurationController)
        
        with Container(id="object_add_box"):
            with Horizontal(id="select"):
                yield Input(id="uid_input", placeholder="Object ID")
                yield Select([(c, c) for c in self._config_controller.get_list_of_classes()],
                                id="class_select", allow_blank=True)
                # with Horizontal(classes="buttons"):
                    # Add buttons
            yield Button("Add Object", id="add_obj", variant="success")
            yield Button("Cancel", id="cancel", variant="error")

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id=="add_obj":
            self.add_object()
        else:
            self.app.screen.dismiss()
    
    def add_object(self):
        input = self.query_one(Input)
        selection = self.query_one(Select)
        
        uid = input.value
        config_class = selection.value
        
        if uid and not selection.is_blank():
            self._config_controller.add_new_conf_obj(config_class, uid)

            self.dismiss_and_update()
        
    def dismiss_and_update(self):
        selection_menu = self._main_screen.query_exactly_one("SelectionPanel")
        selection_menu.refresh(recompose=True)
        selection_menu.restore_menu_state()
        self.app.screen.dismiss()

    
        
