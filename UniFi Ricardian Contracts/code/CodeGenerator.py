import sys, string


class SyntaxError:
    pass


class CodeGenerator:

    def begin(self, tab="\t"):
        self.code = []
        self.tab = tab
        self.level = 0

    def end(self):
        return "\n".join(self.code)

    def write(self, string):
        self.code.append(self.tab * self.level + string)

    def indent(self):
        self.level = self.level + 1

    def dedent(self):
        if self.level == 0:
            raise SyntaxError("internal error in code generator")
        self.level = self.level - 1

    def write_pragma(self, ver):
        self.code.append(self.tab * self.level + f'pragma solidity {ver};')


class RicardianContract:

    def __init__(self, params, instr, filehash):
        self.hash = filehash
        self.params = params
        self.instr = instr
        self.c = CodeGenerator()

    def generate(self, filename):
        if self.instr == ('debt instrument', 'fixed'):
            self._debt_instrument_fixed(filename)
        if self.instr == ('multiplier', 'simple'):
            self._money_multiplier_simple(filename)

    def _debt_instrument_fixed(self, filename):
        self.c = CodeGenerator()
        self.c.begin()
        # secret
        f = open(filename, 'w')
        f.write(self.c.end())
        f.close()

    def _money_multiplier_simple(self, filename):
        self.c = CodeGenerator()
        self.c.begin()
        # secret
        f = open(filename, 'w')
        f.write(self.c.end())
        f.close()
