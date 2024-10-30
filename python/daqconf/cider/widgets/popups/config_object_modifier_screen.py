
from daqconf.cider.widgets.modify_config_relations import RelationshipSelectPanel
from daqconf.cider.widgets.config_table import ConfigTable
from daqconf.cider.widgets.configuration_controller import ConfigurationController

from textual.containers import Grid
from textual.screen import ModalScreen
from textual.widgets import Button
from os import environ


class ConfigObjectModifierScreen(ModalScreen):
    css_file_path = f"{environ.get('DAQCONF_SHARE')}/config/textual_dbe/textual_css"

    CSS_PATH = f"{css_file_path}/modify_object_layout.tcss"

    def compose(self):

        # main_screen = self.app.get_screen("main")
        # self._config_controller = main_screen.query_one(ConfigurationController)
        # self._logger = main_screen.query_one("main_log")

        # ConfigTable(id="sub_config_table"),
        yield RelationshipSelectPanel(id="rel_select")
        yield Button("Exit", variant="success", id="exit")
        
    def on_button_pressed(self, event: Button.Pressed)->None:
        if event.button.id=="exit":
            
            rel_panel = self.query_one(RelationshipSelectPanel)

        
            rel_panel.verify_relations()
            # except Exception as e:
            #     self._logger.write_error(e)

            self.app.screen.dismiss()

