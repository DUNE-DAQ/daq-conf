# Simple widget for editing XML files when conffwk fails you, 
# annoyingly right now Textual doesn't have xml syntax highlighting
# for future reference it does live here: https://github.com/tree-sitter-grammars

from textual.widgets import TextArea, Static

class DirectConfigurationEditor(Static):
    def Compose(self):
        yield TextArea.code_editor()