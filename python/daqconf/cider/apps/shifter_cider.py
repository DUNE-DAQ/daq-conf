from typing import Type
from textual.app import App
from textual.driver import Driver
from daqconf.cider.screens.shifter_cider_session_select_screen import ShifterSelectionScreen
from daqconf.cider.screens.disable_object_toggle_screen import DisableObjectToggleScreen
from textual import on, work

class ShifterCider(App):
    def __init__(self, session_folder, driver_class: type[Driver] | None = None, css_path: str | None = None, watch_css: bool = False, ansi_color: bool = False):
        super().__init__(driver_class, css_path, watch_css, ansi_color)
        self._session_folder = session_folder
        self._exit_message = ""
        
    def exit_message(self):
        return self._exit_message
        
    @work
    async def on_mount(self):
        self.install_screen(ShifterSelectionScreen(self._session_folder), name="main")
        self.install_screen(DisableObjectToggleScreen(), name="disable")

        self.push_screen("main")

    def set_input_folder(self, input_folder_name: str):
        self._input_folder_name = input_folder_name
    
    def exit(self, message: str | None = None) -> None:
        """Override the exit method to store the exit message."""
        self._exit_message = message
        super().exit()  # Call the original exit method

    async def on_shutdown(self) -> None:
        """Called when the application exits."""
        print(f"Exiting application with message: {self._exit_message}")
        
