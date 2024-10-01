from typing import Coroutine
from textual_oks.widgets.configuration_controller import ConfigurationController

from textual.widgets import Static, Tree
from textual.widgets.tree import TreeNode

from typing import Any

class SelectionMenu(Static):
    '''
    Basic selection menu, builds tree from selection objects
    '''
    _tree = None
    
    def compose(self):        
        self._build_tree()
        yield self._tree
    
    def _build_tree(self):
        # Iteratively builds tree via dictionary
        self._tree = Tree(f"File Browser:")
        main_screen = self.app.get_screen("main")
        self._controller = main_screen.query_one("ConfigurationController")

        for key, interface in self._controller.get_interface().items():
            interface.recompose()

        
        main_screen = self.app.get_screen("main")
        self._controller = main_screen.query_one("ConfigurationController")
        
        if self.id not in self._controller.get_interface().keys():
            raise ValueError(f"Cannot find {self._interface_label} in controller. \n  \
                             available interfaces are {self._controller.get_interface()}")
        
        tree_root = self._tree.root
        tree_root.expand()
        
        # Sort out the tree        
        for key, branch in sorted(self._controller.get_interface()[self.id].relationships.items()):
            tree_node = tree_root.add(f"[green]{key}[]", expand=False)
            self.__build_tree_node(tree_node, branch)
            

    def __build_tree_node(self, input_node: TreeNode, input_list: list):
        if len(input_list)==0:
            input_node.remove()

        for config_item in input_list:
            if isinstance(config_item, dict):
                dal_str = self._controller.generate_rich_string(list(config_item.keys())[0])
                tree_node = input_node.add(dal_str, data=list(config_item.keys())[0])

                self.__build_tree_node(tree_node, list(config_item.values())[0])
            else:
                input_node.add_leaf(self._controller.generate_rich_string(config_item), data=config_item)

    def on_tree_node_selected(self, event):
        controller:ConfigurationController = self.app.query_one("ConfigurationController")
        
        if event.node.data is not None: 
            controller.current_dal = event.node.data