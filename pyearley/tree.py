from ete3 import Tree, TreeNode
from pyearley.rule import Symbol

def prune(tree, symbols, preserve_branch_length=False):
    def _preprocess(nodes):
        for node in nodes:
            if issubclass(node.__class__, Symbol):
                yield node.name
            else:
                yield node

    symbol_set = set(_preprocess(symbols))
    nodes = []

    for t_node in tree.traverse():
       if t_node.name in symbol_set:
           nodes.append(t_node)

    return tree.prune(nodes, preserve_branch_length)

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
                tree_node.add_feature("tokens", [token])
            elif parse_node["type"] == "internal":
                symbol = parse_node["symbol"]
                rule = parse_node["rule"]
                children = parse_node["children"]
                token = []

                for child_node in children:
                    node = _build(child_node)
                    tree_node.add_child(node)
                    token.extend(node.tokens)

                tree_node.name = symbol
                tree_node.add_feature("rule", rule)
                tree_node.add_feature("tokens", token)

            return tree_node

        return _build(parse_node, Tree())
