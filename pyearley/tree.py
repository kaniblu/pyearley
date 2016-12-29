from ete3 import Tree, TreeNode
from pyearley.rule import Symbol

class InternalNode(object):
    def __init__(self, rule, children):
        self.rule = rule
        self.symbol = rule[0]
        self.rhs = rule[1:]
        self.children = list(set(children))
        self.children_hash = [hash(child) for child in self.children]
        self.children, self.children_hash = zip(*sorted(zip(self.children, self.children_hash), key=lambda x: x[1]))

    def __hash__(self):
        return sum(self.children_hash) * 0x774 + hash(self.rule)

    def __eq__(self, other):
        if isinstance(other, InternalNode):
            return self.rule == other.rule and len(self.children) == len(other.children) and all(map(lambda x: x[0] == x[1], zip(self.children, other.children)))
        else:
            return False

    def __repr__(self):
        return "InternalNode ({} -> {}) ({} children)".format(self.symbol, self.rhs, len(self.children))

class LeafNode(object):
    def __init__(self, literal, token):
        self.literal = literal
        self.token = token

    def __hash__(self):
        return hash(self.literal) * 0x3523 + hash(self.token)

    def __eq__(self, other):
        return isinstance(other, LeafNode) and self.literal, self.token == other.literal, other.token

    def __repr__(self):
        return "LeafNode ({}: {})".format(self.literal, self.token)

def search(tree, name=None, func=None, **kwargs):
    for node in tree.traverse():
        ret = False
        if name is not None and node.name == name:
            ret = True
        elif func is not None and func(node):
            ret = True
        else:
            for k, v in kwargs.items():
                if getattr(node, k) == v:
                    ret = True
                    break

        if ret:
            yield node

def prune(tree, symbol):
    def _preprocess(nodes):
        for node in nodes:
            if issubclass(node.__class__, Symbol):
                yield node.name
            else:
                yield node

    def _prune_node(node):
        ancestors = node.get_ancestors()

        if not ancestors:
            return False

        parent = ancestors[0]
        desc = node.children

        parent.remove_child(node)
        for d in desc:
            parent.add_child(d)

        return True

    temp_symbols = symbol.get_temp_symbols()
    temp_nodes = search(tree, func=lambda x: x.name in temp_symbols)

    for temp_node in temp_nodes:
        _prune_node(temp_node)
    # symbol_set = set(_preprocess(symbols))
    # nodes = []
    #
    # for t_node in tree.traverse():
    #    if t_node.name in symbol_set:
    #        nodes.append(t_node)
    #
    # return tree.prune(nodes, preserve_branch_length)

class GraphBuilder(object):
    def __init__(self):
        pass

    def build(self, parse_node):
        def _build(parse_node, tree_node=None):
            if tree_node is None:
                tree_node = TreeNode()

            if isinstance(parse_node, list):
                print(parse_node)

            if isinstance(parse_node, LeafNode):
                symbol = parse_node.literal
                token = parse_node.token

                tree_node.name = symbol
                tree_node.add_feature("tokens", [token])
            elif isinstance(parse_node, InternalNode):
                symbol = parse_node.symbol
                rule = parse_node.rule
                children = parse_node.children
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
