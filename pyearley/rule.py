# encoding: UTF-8

import random
import string

# Create abstracted context-free grammars
# Follows pyparsing style constructors

_NAME_HISTORY = set()


def _create_random_name(l=6):
    name = None

    while name is None and name not in _NAME_HISTORY:
        name = "SYM_{}".format("".join([random.choice(string.ascii_letters + string.digits) for i in range(l)]))

    _NAME_HISTORY.add(name)

    return name


# basic form

class Symbol():
    def __init__(self, name=None, is_terminal=False):
        if name is None:
            name = _create_random_name()

        self.set_name(name)
        self.is_terminal = is_terminal
        self.rhs = []

    def set_name(self, name):
        _NAME_HISTORY.add(name)
        self.name = name

        return self

    def add_rhs(self, symbol):
        if self.is_terminal:
            raise SyntaxError()

        self.rhs.append(symbol)

        return self

    def __len__(self):
        return len(self.rhs)

    def __add__(self, other):
        return And().add_rhs(self).add_rhs(other)

    def __or__(self, other):
        return Or().add_rhs(self).add_rhs(other)

class TerminalSymbol(Symbol):
    def __init__(self, name=None):
        super(TerminalSymbol, self).__init__(name, True)

class NonterminalSymbol(Symbol):
    def __init__(self, name=None):
        super(NonterminalSymbol, self).__init__(name, False)
        self._converted = False

    def to_earley_ruleset(self):
        if self._converted:
            return set()

        self._converted = True

        ruleset = set()

        for symbol in self.rhs:
            if issubclass(symbol.__class__, NonterminalSymbol):
                ruleset |= symbol.to_earley_ruleset()

        return ruleset

class Forward(NonterminalSymbol):
    def __init__(self, *args, **kwargs):
        super(Forward, self).__init__(*args, **kwargs)

    def to_earley_ruleset(self):
        ruleset = {(self.name, self.rhs[0].name)}
        ruleset |= super(Forward, self).to_earley_ruleset()

        return ruleset

    def __lshift__(self, other):
        self.add_rhs(other)
        return self

class Or(NonterminalSymbol):
    def __init__(self, *args, **kwargs):
        super(Or, self).__init__(*args, **kwargs)

    def to_earley_ruleset(self):
        ruleset = {(self.name, symbol.name) for symbol in self.rhs}
        ruleset |= super(Or, self).to_earley_ruleset()

        return ruleset


class And(NonterminalSymbol):
    def __init__(self, *args, **kwargs):
        super(And, self).__init__(*args, **kwargs)

    def to_earley_ruleset(self):
        ruleset = {(self.name,) + tuple(symbol.name for symbol in self.rhs)}
        ruleset |= super(And, self).to_earley_ruleset()

        return ruleset

class OneOrMore(NonterminalSymbol):
    def __init__(self, *args, **kwargs):
        super(OneOrMore, self).__init__(*args, **kwargs)

    def to_earley_ruleset(self):
        ruleset = {(self.name, self.rhs[0].name, self.name),
                   (self.name, self.rhs[0].name)}
        ruleset |= super(OneOrMore, self).to_earley_ruleset()

        return ruleset

class ZeroOrMore(OneOrMore):
    def __init__(self, *args, **kwargs):
        super(ZeroOrMore, self).__init__(*args, **kwargs)

    def to_earley_ruleset(self):
        return super(ZeroOrMore, self).to_earley_ruleset() | {(self.name, )}

class Optional(NonterminalSymbol):
    def __init__(self, *args, **kwargs):
        super(Optional, self).__init__(*args, **kwargs)

    def to_earley_ruleset(self):
        ruleset = {(self.name, self.rhs[0].name), (self.name, )}
        ruleset |= super(Optional, self).to_earley_ruleset()

        return ruleset

Literal = TerminalSymbol

def one_of(literal_choices):
    symbol = Or()
    for choice in literal_choices:
        symbol.add_rhs(Literal(choice))

    return symbol

def main():
    # A -> B X | Y
    # B -> A W | U

    A = Forward("A")
    B = Forward("B")

    A << ((B + Literal("X")) | Literal("Y"))
    B << ((A + Literal("W")) | Literal("U"))

    rules = list(A.to_earley_ruleset())

    import pprint
    from pyearley import earley

    pprint.pprint(rules)

    ep = earley.EarleyParser(rules)
    pprint.pprint(ep.parse("YWX", "A", debug=True))


if __name__ == "__main__":
    main()
