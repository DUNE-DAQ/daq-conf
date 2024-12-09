from daqconf.cider.widgets.configuration_controller import ConfigurationController
from daqconf.cider.widgets.file_io import OpenFile, RenameConfigObject, SaveWithMessage
from daqconf.cider.screens.popup_screen_base import PopupScreenBase
from daqconf.cider.widgets.disable_session_select import DisableSessionSelect

# Derived screens
class SaveWithMessageScreen(PopupScreenBase):
    def __init__(self, name=None, id=None, classes=None):
        super().__init__(SaveWithMessage, "save_menu_layout.tcss", name, id, classes)


class OpenFileScreen(PopupScreenBase):
    def __init__(self, name=None, id=None, classes=None):
        super().__init__(OpenFile, "save_menu_layout.tcss", name, id, classes)
        self._controller = self._get_main_screen_controller()

    def _get_main_screen_controller(self):
        main_screen = self.app.get_screen("main")
        return main_screen.query_one(ConfigurationController)

class RenameConfigObjectScreen(PopupScreenBase):
    def __init__(self, name=None, id=None, classes=None):
        super().__init__(RenameConfigObject, "save_menu_layout.tcss", name, id, classes)

class SelectSessionScreen(PopupScreenBase):
    def __init__(self, name=None, id=None, classes=None):
        super().__init__(DisableSessionSelect, "session_selection_layout.tcss", name, id, classes)
