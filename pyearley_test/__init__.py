from pyearley import *

def main():

    A = Forward("A")
    B = Forward("B")

    A << ((B + Literal("X")) | Literal("Y"))
    B << ((A + Literal("W")) | Literal("U"))

    parser = EarleyParser(A)
    trees = parser.parse("YWXWXWXWX", "A")

    print([tree.write(features=["tokens"]) for tree in trees])

if __name__ == "__main__":
    main()