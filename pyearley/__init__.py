from pyearley.earley import EarleyParser as PureEarleyParser
from pyearley.rule import OneOrMore, ZeroOrMore, Optional, Literal, Forward, one_of

class EarleyParser():
    def __init__(self, pyearley_rules):
        expanded_rules = pyearley_rules.to_earley_ruleset()
        self.parser = PureEarleyParser(expanded_rules)

    def parse(self, tokens, target_symbol):
        trees = self.parser.parse(tokens, target_symbol, should_traceback=True)
        [trees]