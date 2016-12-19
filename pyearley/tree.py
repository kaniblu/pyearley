from ete3 import Tree

class _GraphBuilder(object):
    def __init__(self):
        self.index = 0

    def get_new_id(self):
        i = self.index
        self.index += 1

        return i

    def build(self, tree):
        nodes, edges = [], []

        if tree["type"] == "leaf":
            node = (self.get_new_id(), tree["value"])
            nodes.append(node)
            root = node

        elif tree["type"] == "internal":
            rule = tree["rule"]
            lhs = rule[0]
            rhs = rule[1:]
            root = (self.get_new_id(), lhs)

            children = []
            for c in tree["children"]:
                c_root, c_nodes, c_edges = self.build(c)
                nodes.extend(c_nodes)
                edges.extend(c_edges)
                children.append(c_root)

            for c in children:
                edges.append((root, c))

            nodes.append(root)

        else:
            raise ValueError()

        return root, nodes, edges


class Graph(object):
    def __init__(self, parse_tree):
        builder = _GraphBuilder()
        self.root, self.nodes, self.edges = builder.build(parse_tree)

        # Cache in dictionary
        self.edge_map = {}
        for a, b in self.edges:
            if a not in self.edge_map:
                self.edge_map[a] = []
            self.edge_map[a].append(b)

        self.build_tree()

    def __getitem__(self, item):
        return self.edge_map.__getitem__(item)

    def __contains__(self, item):
        return self.edge_map.__contains__(item)

    def build_tree(self):
        def _build_tree(tree, name):
            t = tree.add_child(name="({}, {})".format(*name))
            if name in self.edge_map:
                for n in self.edge_map[name]:
                    _build_tree(t, n)
            return t
        self.tree = Tree()
        _build_tree(self.tree, self.root)

    def save(self, filename, **kwargs):
        self.tree.render(filename, **kwargs)

    def _find_nodes(self, name):
        def __find_nodes(tree, name):
            results = set()
            if tree.name == name:
                results.add(tree)

            for c in tree.children:
                results.update(__find_nodes(c, name))

            return results

        return __find_nodes(self.tree, name)

    def prune_nodes(self, retained_symbols):
        nodes = list(map(lambda x: "({}, {})".format(*x), filter(lambda x: x[1] in retained_symbols, self.nodes)))
        self.tree.prune(nodes)
