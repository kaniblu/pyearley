from pyearley.earley import EarleyParser as PureEarleyParser
from pyearley.rule import OneOrMore, ZeroOrMore, Optional, Literal, Forward, one_of
from pyearley.tree import prune

class EarleyParser():
    def __init__(self, pyearley_rules):
        self.rules = pyearley_rules
        self.symbols = self.rules.get_real_symbols()

        expanded_rules = pyearley_rules.get_expanded_ruleset()
        self.parser = PureEarleyParser(expanded_rules)

    def parse(self, tokens, target_symbol):
        trees = self.parser.parse(tokens, target_symbol, should_traceback=True)

        for tree in trees:
            prune(tree, self.symbols)

        return trees