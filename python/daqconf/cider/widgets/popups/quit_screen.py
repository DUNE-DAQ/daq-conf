from textual.widgets import Button, Label
from textual.screen import Screen
from textual.containers import Grid
from textual.app import ComposeResult
from os import environ

class QuitScreen(Screen):
    """Screen with a dialog to quit."""
    css_file_path = f"{environ.get('DAQCONF_SHARE')}/config/textual_dbe/textual_css"

    CSS_PATH = f"{css_file_path}/quit_screen.tcss"

    def compose(self) -> ComposeResult:
        yield Grid(
            Label("Are you sure you want to quit? [Any unsaved changes will be lost!]", id="question"),
            Button("Quit", variant="error", id="quit"),
            Button("Cancel", variant="primary", id="cancel"),
            id="dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "quit":
            self.app.exit()
        else:
            self.app.pop_screen()
