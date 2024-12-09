from os import environ

from textual.app import ComposeResult
from textual.screen import Screen


class ConfigurableScreenMixin:
    """Mixin to provide common configuration for screens."""
    CSS_BASE_PATH = f"{environ.get('DAQCONF_SHARE')}/config/textual_dbe/textual_css"

    @classmethod
    def get_css_path(cls, css_file_name: str) -> str:
        return f"{cls.CSS_BASE_PATH}/{css_file_name}"


class PopupScreenBase(Screen, ConfigurableScreenMixin):
    """Base class for shared screen behaviors."""

    def __init__(self, content_widget_cls, css_file_name, name=None, id=None, classes=None):
        super().__init__(name=name, id=id, classes=classes)
        self.CSS_PATH = self.get_css_path(css_file_name)
        self._content_widget_cls = content_widget_cls

    def compose(self) -> ComposeResult:
        yield self._content_widget_cls()

    def on_mount(self) -> None:
        widget = self.query_one(self._content_widget_cls)
        widget.focus()