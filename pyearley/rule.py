# encoding: UTF-8

import random
import string, functools

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
    def __init__(self, name=None, is_terminal=False, is_temp=None):
        if name is None:
            name = _create_random_name()
            self.is_temp = True
        else:
            self.is_temp = False

        if is_temp is not None:
            self.is_temp = is_temp

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

    def _get_real_symbols(self, visited):
        if self in visited:
            return set()

        visited.add(self)

        if self.rhs:
            return functools.reduce(lambda x, y: x | y, [s._get_real_symbols(visited) for s in self.rhs], set())
        elif self.is_temp:
            return set()
        else:
            return {self.name}

    def get_real_symbols(self):
        return self._get_real_symbols(set())

    def ignore(self):
        self.is_temp = True
        return self

    def attend(self):
        self.is_temp = False
        return self

    def __len__(self):
        return len(self.rhs)

    def __add__(self, other):
        return And().add_rhs(self).add_rhs(other)

    def __or__(self, other):
        return Or().add_rhs(self).add_rhs(other)

class TerminalSymbol(Symbol):
    def __init__(self, name=None, **kwargs):
        super(TerminalSymbol, self).__init__(name, True, **kwargs)

class NonterminalSymbol(Symbol):
    def __init__(self, name=None, **kwargs):
        super(NonterminalSymbol, self).__init__(name, False, **kwargs)

    def _get_expanded_ruleset(self, visited):

        if self in visited:
            return set()

        visited.add(self)

        ruleset = set()

        for symbol in self.rhs:
            if issubclass(symbol.__class__, NonterminalSymbol):
                ruleset |= symbol._get_expanded_ruleset(visited)

        ruleset |= self.expand()

        return ruleset

    def get_expanded_ruleset(self):
        return self._get_expanded_ruleset(set())

    def expand(self):
        raise NotImplementedError()

class Forward(NonterminalSymbol):
    def __init__(self, *args, **kwargs):
        super(Forward, self).__init__(*args, **kwargs)

    def expand(self):
        ruleset = {(self.name, self.rhs[0].name)}

        return ruleset

    def __lshift__(self, other):
        self.add_rhs(other)
        return self

class Or(NonterminalSymbol):
    def __init__(self, *args, **kwargs):
        super(Or, self).__init__(*args, **kwargs)

    def expand(self):
        ruleset = {(self.name, symbol.name) for symbol in self.rhs}

        return ruleset


class And(NonterminalSymbol):
    def __init__(self, *args, **kwargs):
        super(And, self).__init__(*args, **kwargs)

    def expand(self):
        ruleset = {(self.name,) + tuple(symbol.name for symbol in self.rhs)}

        return ruleset

class OneOrMore(NonterminalSymbol):
    def __init__(self, *args, **kwargs):
        super(OneOrMore, self).__init__(*args, **kwargs)

    def expand(self):
        ruleset = {(self.name, self.rhs[0].name, self.name),
                   (self.name, self.rhs[0].name)}

        return ruleset

class ZeroOrMore(OneOrMore):
    def __init__(self, *args, **kwargs):
        super(ZeroOrMore, self).__init__(*args, **kwargs)

    def expand(self):
        return {(self.name,)}

class Optional(NonterminalSymbol):
    def __init__(self, *args, **kwargs):
        super(Optional, self).__init__(*args, **kwargs)

    def expand(self):
        ruleset = {(self.name, self.rhs[0].name), (self.name, )}\

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

    A << ((B + Literal("X").ignore()) | Literal("Y").ignore())
    B << ((A + Literal("W").ignore()) | Literal("U").ignore())

    symbols = A.get_real_symbols()
    expanded_rules = A.get_expanded_ruleset()

    print(symbols)
    print(expanded_rules)

if __name__ == "__main__":
    main()
