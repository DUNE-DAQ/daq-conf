from textual.widgets import Select, Static
import os
import xml.etree.ElementTree as ET
from typing import List
from daqconf.cider.data_structures.structured_configuration import StructuredConfiguration
from daqconf.cider.data_structures.configuration_handler import ConfigurationHandler

class SelectFile(Static):
    def __init__(self, session_directories: str | List[str] = "", session_only: bool = False, renderable = "", *, expand: bool = False, shrink: bool = False, markup: bool = True, name: str | None = None, id: str | None = None, classes: str | None = None, disabled: bool = False) -> None:
        super().__init__(renderable, expand=expand, shrink=shrink, markup=markup, name=name, id=id, classes=classes, disabled=disabled)

        self._database_list = self.generate_selection_list(session_directories, session_only)

    @classmethod
    def generate_selection_list(cls, session_directories: str | List[str] = "", session_only: bool = True):
        # Firstly find all databases
        
        # db_path = os.environ.get('DUNEDAQ_DB_PATH')
        # database_list = os.listdir(db_path)
                
        database_list = []
        if isinstance(session_directories, str):
            if not session_directories:
                session_directories = [os.getcwd()]
            else:
                session_directories=[session_directories]
        
        
        for directory in session_directories:
            database_list+=[f"{directory}/{i}" for i in os.listdir(directory) if i.endswith(".data.xml")] 
        
        # For the simplified DB editor view we only want to show configurations containing sessions
        # while we're here we might as well cache the number of sessions
        
        if session_only:
            database_list = [(file, cls.get_number_of_sessions(file))
                             for file in database_list if cls.get_number_of_sessions(file)]
    
        return database_list

    @classmethod
    def get_number_of_sessions(cls, config_file_path: str)->int:
        # For now let's just search for "Session"... this is hacky but oh well
        # Open as config file
        try:
            config_file = ConfigurationHandler(config_file_path)
            n_sessions = len(config_file.get_conf_objects_class("Session"))        
        except:
            n_sessions = 0

        # Get total nimber of sesions in the config
        return n_sessions

    # Yield everything
    def compose(self):
        options = [(os.path.basename(f[0]), f) for f in self._database_list]
        yield Select(options, prompt="Select a Configuration File", id="config_file_select")
    
class SelectSession(Static):
    def __init__(self, input_database: str = "", renderable = "", *, expand: bool = False, shrink: bool = False, markup: bool = True, name: str | None = None, id: str | None = None, classes: str | None = None, disabled: bool = False) -> None:
        super().__init__(renderable, expand=expand, shrink=shrink, markup=markup, name=name, id=id, classes=classes, disabled=disabled)
        
        self._select_widget = Select(options=([]), id="session_select", prompt="Select a Session")
        
    def change_config(self, input_database):
        # Create Session
        sessions = []

        if input_database:
            self._structured_config = StructuredConfiguration(input_database)            
            sessions = self._structured_config.configuration_handler.get_conf_objects_class("Session")
        
        self._selection_list = [(getattr(s, 'id'), s) for s in sessions]
        self._select_widget.set_options(self._selection_list)
                
        
    def compose(self):
        yield self._select_widget
        