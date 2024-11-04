from textual.widgets import Button, Label
from textual.screen import Screen
from textual.containers import Grid
from textual.app import ComposeResult
from os import environ

from daqconf.cider.widgets.configuration_controller import ConfigurationController

class DeleteConfigObjectScreen(Screen):
    
    css_file_path = f"{environ.get('DAQCONF_SHARE')}/config/textual_dbe/textual_css"

    CSS_PATH = f"{css_file_path}/delete_screen.tcss"


    def compose(self) -> ComposeResult:
        self._main_screen = self.app.get_screen("main")
        self._config_controller: ConfigurationController = self._main_screen.query_one(ConfigurationController)

        selected_obj = getattr(self._config_controller.current_dal, "id")
        
        yield Grid(
            
            Label(f"Are you sure you want to delete {selected_obj}?]", id="question"),
            Button("Delete", variant="success", id="delete"),
            Button("Cancel", variant="primary", id="cancel"),
            id="dialog",
        )

    # Need to move this somewhere
    def dismiss_and_update(self):
        selection_menu = self._main_screen.query_exactly_one("SelectionPanel")
        selection_menu.refresh(recompose=True)
        selection_menu.restore_menu_state()
        self.app.screen.dismiss()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "delete":
            self._config_controller.destroy_current_object()
            self.dismiss_and_update()
        else:
            self.app.pop_screen()
