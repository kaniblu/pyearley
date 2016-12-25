from ete3 import Tree, TreeNode

class GraphBuilder(object):
    def __init__(self):
        pass

    def build(self, parse_node):
        def _build(parse_node, tree_node=None):
            if tree_node is None:
                tree_node = TreeNode()

            if parse_node["type"] == "leaf":
                symbol = parse_node["symbol"]
                token = parse_node["token"]

                tree_node.name = symbol
                tree_node.add_feature("token", token)
            elif parse_node["type"] == "internal":
                symbol = parse_node["symbol"]
                rule = parse_node["rule"]
                children = parse_node["children"]

                for child_node in children:
                    node = _build(child_node)
                    tree_node.add_child(node)

                tree_node.name = symbol
                tree_node.add_feature("rule", rule)

            return tree_node

        return _build(parse_node, Tree())
