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


class _Symbol(object):
    "The basic unit of cfg"

    def __init__(self, terminal, name=None):
        self.terminal = terminal

        if name is None:
            name = _create_random_name()

        self.set_name(name)

    def set_body(self, symbols_or_token):
        self.body = symbols_or_token
        return self

    def set_name(self, name):
        self.name = name
        _NAME_HISTORY.add(name)

        return self

    def is_terminal(self):
        return self.terminal

    def _expand(self):
        if isinstance(self, OneOrMore):
            s1 = (self.name, self.body[0].name, self.name)
            s2 = (self.name, self.body[0].name)

            return {s1, s2}
        elif isinstance(self, ZeroOrMore):
            s1 = (self.name, self.body[0].name, self.name)
            s2 = (self.name, self.body[0].name)
            s3 = (self.name,)

            return {s1, s2, s3}
        elif isinstance(self, Optional):
            s1 = (self.name, self.body[0].name)
            s2 = (self.name,)

            return {s1, s2}
        elif isinstance(self, And):
            return {(self.name,) + tuple([b.name for b in self.body])}
        elif isinstance(self, Or):
            return [(self.name, b.name) for b in self.body]
        elif isinstance(self, Literal):
            return None

    def to_ruleset(self):
        ruleset = set()

        if self.is_terminal():
            pass
        else:
            ruleset.update(self._expand())
            for s in self.body:
                ruleset |= s.to_ruleset()

        return ruleset

    def __add__(self, other):
        return And(self, other)

    def __and__(self, other):
        return And(self, other)

    def __or__(self, other):
        return Or(self, other)


class _UnarySymbol(_Symbol):
    def __init__(self, symbol):
        super(_UnarySymbol, self).__init__(False)
        self.set_body((symbol,))


class _BinarySymbol(_Symbol):
    def __init__(self, s1, s2):
        super(_BinarySymbol, self).__init__(False)
        self.set_body((s1, s2))


class _NarySymbol(_Symbol):
    def __init__(self, *symbols):
        super(_NarySymbol, self).__init__(False)
        self.set_body(symbols)


# External Symbols

class Literal(_Symbol):
    def __init__(self, token):
        super(Literal, self).__init__(True)
        self.set_body(token)
        self.set_name(token)


class OneOrMore(_UnarySymbol):
    def __init__(self, symbol):
        super(OneOrMore, self).__init__(symbol)


class ZeroOrMore(_UnarySymbol):
    def __init__(self, symbol):
        super(ZeroOrMore, self).__init__(symbol)


class Or(_NarySymbol):
    def __init__(self, *symbols):
        super(Or, self).__init__(*symbols)


class LiteralChoice(Or):
    def __init__(self, tokens):
        super(LiteralChoice, self).__init__(*[Literal(token) for token in tokens])


class And(_NarySymbol):
    def __init__(self, *symbols):
        super(And, self).__init__(*symbols)


class Optional(_UnarySymbol):
    def __init__(self, symbol):
        super(Optional, self).__init__(symbol)


def main():
    x = OneOrMore(LiteralChoice("ABC")).set_name("S")
    rules = list(x.to_ruleset())

    import pprint
    from pyearley import earley

    pprint.pprint(rules)

    ep = earley.EarleyParser(rules)
    pprint.pprint(ep.parse("ABCBACBAB", "S", debug=True))


if __name__ == "__main__":
    main()
