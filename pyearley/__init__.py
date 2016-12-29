from pyearley.earley import EarleyParser as PureEarleyParser
from pyearley.rule import OneOrMore, ZeroOrMore, Optional, Literal, Forward, Or, And, one_of, optional, star, plus
from pyearley.tree import prune

class EarleyParser():
    def __init__(self, pyearley_rules):
        self.rules = pyearley_rules

        expanded_rules = pyearley_rules.get_expanded_ruleset()
        self.parser = PureEarleyParser(expanded_rules)

    def parse(self, tokens, target_symbol, **kwargs):
        trees = self.parser.parse(tokens, target_symbol, should_traceback=True, **kwargs)

        for tree in trees:
            prune(tree, target_symbol)

        return trees