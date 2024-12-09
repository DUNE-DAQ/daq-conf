from daqconf.cider.widgets.add_objects import AddNewObject


from textual.app import ComposeResult
from textual.screen import ModalScreen


from os import environ


class AddNewObjectScreen(ModalScreen[bool]):
    css_file_path = f"{environ.get('DAQCONF_SHARE')}/config/textual_dbe/textual_css"

    CSS_PATH = f"{css_file_path}/add_object_layout.tcss"
    """
    Splash screen for adding configuration
    """

    def compose(self)->ComposeResult:
        yield AddNewObject()

    def on_mount(self) -> None:
        message_box = self.query_one(AddNewObject)
        message_box.focus()