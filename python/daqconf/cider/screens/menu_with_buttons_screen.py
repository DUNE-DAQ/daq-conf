from daqconf.cider.widgets.configuration_controller import ConfigurationController
from daqconf.cider.widgets.file_io import OpenFile, RenameConfigObject, SaveWithMessage


from textual.app import ComposeResult
from textual.screen import ModalScreen, Screen


from os import environ


class SaveWithMessageScreen(ModalScreen[bool]):
    css_file_path = f"{environ.get('DAQCONF_SHARE')}/config/textual_dbe/textual_css"

    CSS_PATH = f"{css_file_path}/save_menu_layout.tcss"
    """
    Splash screen for saving to file
    """

    def compose(self)->ComposeResult:
        yield SaveWithMessage()

    def on_mount(self) -> None:
        message_box = self.query_one(SaveWithMessage)
        message_box.focus()


class OpenFileScreen(Screen):

    # HACKY WAY TO GET THE CSS TO WORK
    css_file_path = f"{environ.get('DAQCONF_SHARE')}/config/textual_dbe/textual_css"

    CSS_PATH = f"{css_file_path}/save_menu_layout.tcss"

    def __init__(self, name: str | None=None, id: str | None = None, classes: str | None = None) -> None:
        """Add in configuration screen
        """
        super().__init__(name=name, id=id, classes=classes)
        main_screen = self.app.get_screen("main")
        self._controller = main_screen.query_one(ConfigurationController)


    def compose(self)->ComposeResult:
        yield OpenFile()

    def on_mount(self) -> None:
        message_box = self.query_one(OpenFile)
        message_box.focus()


class RenameConfigObjectScreen(Screen):
    css_file_path = f"{environ.get('DAQCONF_SHARE')}/config/textual_dbe/textual_css"

    CSS_PATH = f"{css_file_path}/save_menu_layout.tcss"
    """
    Splash screen for saving to file
    """

    def compose(self)->ComposeResult:
        yield RenameConfigObject()

    def on_mount(self) -> None:
        message_box = self.query_one(RenameConfigObject)
        message_box.focus()