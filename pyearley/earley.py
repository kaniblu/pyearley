#encoding: UTF-8

import functools, copy
from pyearley.tree import GraphBuilder
from pyearley.tree import InternalNode, LeafNode

class Item(object):
    def __init__(self, dot_idx, src_idx, rule_idx):
        self.data = (dot_idx, src_idx, rule_idx)

    def __hash__(self):
        return hash(self.data)

    def __eq__(self, other):
        return isinstance(other, Item) and self.data == other.data

    @property
    def dot_idx(self):
        return self.data[0]

    @property
    def src_idx(self):
        return self.data[1]

    @property
    def rule_idx(self):
        return self.data[2]

    def __repr__(self):
        return "({}, {}, {})".format(*self.data)

    def __getitem__(self, item):
        return self.data.__getitem__(item)

class EarleyParser(object):
    def __init__(self, rules):
        self.rules = list(rules)

        #Manage empty rules separately
        self.empty_rules = [i for i, rule in enumerate(self.rules) if len(rule) == 1]

        #Cache dictionary
        self.rule_dict = {}

        for i, r in enumerate(self.rules):
            if r[0] not in self.rule_dict:
                self.rule_dict[r[0]] = []

            self.rule_dict[r[0]].append(i)

        #All symbol set
        self.vocab = functools.reduce(lambda x, y: x | set(y), self.rules, set())

        #Cache nonterminal symbols
        self.vocab_nonterminal = set([r[0] for r in self.rules])

        #Cache terminal symbols
        self.vocab_terminal = self.vocab.difference(self.vocab_nonterminal)

        #Cache nonterminal symbols for each rule
        #self.rule_nonterminals = [set(r[1:]) & self.vocab_nonterminal for r in self.rules]

        # Setup Traceback
        # data structure for managing tracebacks
        # maps (item, cur_idx) to list of terminal tokens or other (item, cur_idx) tuples
        self._traceback = {}

    def visualize(self, item):
        rule = self.rules[item.rule_idx]
        dot_idx = item.dot_idx

        lhs = rule[0]
        rhs = rule[1:]
        rhs = rhs[:dot_idx] + (".", ) + rhs[dot_idx:]

        return "({}) {} -> {}".format(item.src_idx, lhs, " ".join(rhs))

    def _traceback_add(self, item, state_idx, stack_item, prev_item=None, prev_state_idx=None):
        key = (item, state_idx)

        if key not in self._traceback:
            self._traceback[key] = []

        self._traceback[key].append({"item": stack_item,
                                     "ref": (prev_item, prev_state_idx)})

    def _traceback_init(self, item, state_idx):
        self._traceback[(item, state_idx)] = [{"item": None, "ref": None}]

    def _traceback_create_tree(self, item, state_idx):
        def __traceback_expand(item, state_idx, cache):
            if (item, state_idx) in cache:
                return cache[(item, state_idx)]

            rule = self.rules[item.rule_idx]
            symbol = rule[0]

            candidates = set()

            for path in self._traceback[(item, state_idx)]:
                it = path["item"]
                ref = path["ref"]

                if ref is None:
                    traces = {tuple()}
                else:
                    prev_item, prev_state_idx = ref
                    traces = __traceback_expand(prev_item, prev_state_idx, cache)

                if it is not None:
                    cur_item, cur_state_idx = it

                    if isinstance(cur_item, Item):
                        __traceback_expand(cur_item, cur_state_idx, cache)

                for trace in traces:
                    new_trace = copy.copy(trace)

                    if it is not None:
                        new_trace = new_trace + (it, )

                    candidates.add(new_trace)

            cache[(item, state_idx)] = candidates

            return candidates

        def __traceback_create_tree(cache, item, state_idx):
            if isinstance(item, Item):
                rule = self.rules[item.rule_idx]
                symbol = rule[0]
                candidates = []

                c = cache[(item, state_idx)]

                for trace in c:
                    children = []
                    for c, next_idx in trace:
                        node = __traceback_create_tree(cache, c, next_idx)
                        children.append(node)

                    candidates.append(children)

                return {"type": "internal", "rule": rule, "symbol": symbol, "children": candidates}

            else:
                symbol, token = item
                return {"type": "leaf", "symbol": symbol, "token": token}

        def __iter_nested_list(ll):
            if len(ll) == 0:
                return []

            if len(ll) == 1:
                return [[i] for i in ll[0]]

            it = __iter_nested_list(ll[:-1])
            new_it = [j + [i] for i in ll[-1] for j in it]

            return new_it

        def __traceback_list(candidate_tree):
            if candidate_tree["type"] == "leaf":

                if "children" in candidate_tree:
                    candidate_tree["children"] = []

                return {LeafNode(candidate_tree["symbol"], candidate_tree["token"])}

            if len(candidate_tree["rule"]) == 1:
                return set()

            candidates = candidate_tree["children"]
            results = set()

            for candidate in candidates:
                candidate_listed = [__traceback_list(c) for c in candidate]
                candidate_listed = [l for l in candidate_listed if len(l) > 0]
                comb = __iter_nested_list(candidate_listed)
                for c in comb:
                    node_obj = InternalNode(candidate_tree["rule"], c)
                    results.add(node_obj)

            return results

        cache = {}
        __traceback_expand(item, state_idx, cache)
        candidate_trees = __traceback_create_tree(cache, item, state_idx)
        results = __traceback_list(candidate_trees)

        return results

    def parse(self, tokens, target_symbol, should_traceback=True, debug=False):
        state_sets = [set() for i in range(len(tokens) + 1)]

        self._traceback = {}

        for i, r in enumerate(self.rules):
            item = Item(0, 0, i) #an item is a tuple of dot index, source state index, and the rule index (in self.rules)
            state_sets[0].add(item)

            self._traceback_init(item, 0)

        for cur_state_idx, state_set in enumerate(state_sets):
            if cur_state_idx >= len(tokens):
                token = None
            else:
                token = tokens[cur_state_idx]

            cur_state_set = state_set

            while True:
                new_items = []

                for item in cur_state_set:
                    dot_idx = item[0] #zero index; max at len(rhs)
                    src_state_idx = item[1]
                    rule_idx = item[2]
                    rule = self.rules[rule_idx]

                    lhs = rule[0]
                    rhs = rule[1:]

                    #Encountered completed item
                    if dot_idx >= len(rhs):
                        for it in state_sets[src_state_idx]:
                            it_r = self.rules[it.rule_idx]

                            #Check if the dot is placed at the left of target non-terminal symbol.
                            if it.dot_idx < len(it_r) - 1 and it_r[it.dot_idx + 1] == lhs:
                                new_item = Item(it.dot_idx + 1, it.src_idx, it.rule_idx)
                                self._traceback_add(new_item, cur_state_idx, (item, cur_state_idx), it, src_state_idx)

                                new_items.append(new_item)

                    #Token is none only when the outer loop is at the last iteration.
                    elif token is not None:
                        cur_symbol = rhs[dot_idx]
                        #Encountered terminal node: scan
                        if cur_symbol in self.vocab_terminal:
                            if cur_symbol == token:
                                new_item = Item(dot_idx + 1, src_state_idx, rule_idx)
                                self._traceback_add(new_item, cur_state_idx + 1, ((cur_symbol, token), cur_state_idx), item, cur_state_idx)

                                state_sets[cur_state_idx + 1].add(new_item)

                        #Encountered nonterminal node: predict
                        elif cur_symbol in self.vocab_nonterminal:
                            for new_ridx in self.rule_dict[cur_symbol]:
                                new_item = Item(0, cur_state_idx, new_ridx)
                                new_items.append(new_item)

                                self._traceback_init(new_item, cur_state_idx)

                    for r_idx in self.empty_rules:
                        rule = self.rules[r_idx]
                        lhs = rule[0]
                        item = Item(0, cur_state_idx, r_idx)

                        self._traceback_init(item, cur_state_idx)

                        for it in state_sets[cur_state_idx]:
                            it_r = self.rules[it.rule_idx]

                            # Check if the dot is placed at the left of target non-terminal symbol.
                            if it.dot_idx < len(it_r) - 1 and it_r[it.dot_idx + 1] == lhs:
                                new_item = Item(it.dot_idx + 1, it.src_idx, it.rule_idx)

                                self._traceback_add(new_item, cur_state_idx, (item, cur_state_idx), it, cur_state_idx)

                                new_items.append(new_item)

                if not new_items:
                    break

                #it's time to process a new set of items.
                #but which are really new?
                next_items = set()
                for item in new_items:
                    if item in state_set:
                        continue

                    state_set.add(item)
                    next_items.add(item)

                #swap out the state set for the next iteration.
                cur_state_set = next_items

            if debug:
                print("==={}===".format(cur_state_idx))
                for i, item in enumerate(state_set):
                    print("{}. {}".format(i + 1, self.visualize(item)))


        final_items = []

        for item in state_sets[-1]:
            if item.src_idx != 0:
                continue

            rule = self.rules[item.rule_idx]

            if rule[0] == target_symbol.name and item.dot_idx >= len(rule) - 1:
                final_items.append(item)

        if should_traceback:
            trees = [self._traceback_create_tree(item, len(tokens)) for item in final_items]
            trees = [t for tree_l in trees for t in tree_l]

            graph_builder = GraphBuilder()

            ret = []
            for t in trees:
                tree = graph_builder.build(t)
                ret.append(tree)
        else:
            ret = len(final_items) > 0

        # Clean up
        del state_sets

        return ret