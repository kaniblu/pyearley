from pyearley import *

def ruleset1():
    """
    Recursion Testing
    A -> B X | Y
    B -> B Z | Y
    """
    A = Forward("A")
    B = Forward("B")

    A << ((B + Literal("X")) | Literal("Y"))
    B << ((A + Literal("Z")) | Literal("Y"))

    return A, B

def ruleset2():
    """
    Ambiguity Testing
    B -> X Y?
    A -> (B | X) Y?
    """
    B = Literal("X") + optional(Literal("Y"))
    A = (B | Literal("X")) + optional(Literal("Y"))

    B.set_name("B")
    A.set_name("A")

    return A

def ruleset3():
    """
    Ambiguity Testing
    B -> X Y
    C -> X Y
    A -> B | C
    """
    B = Literal("X") + Literal("Y")
    C = Literal("Y") + Literal("X")
    A = (star(B) + Literal("X")) | (Literal("X") + star(C))

    B.set_name("B")
    C.set_name("C")
    A.set_name("A")

    return A

def ruleset4():
    t_DET = Forward("DET")  # 관형사
    t_NOUN = Forward("NOUN")  # 체언
    t_ADV = Forward("ADV")  # 부사
    t_ADJ = Forward("ADJ")
    t_VERB = Forward("VERB")
    t_PRED = Forward("PRED")  # 용언
    t_NP = Forward("NP")  # 체언 구문
    t_PP = Forward("PP")  # 용언 구문
    t_ROOT = Forward("ROOT")  # 어근
    t_NP_PP_J = Forward("CL_J")
    t_CLAUSE = Forward("CL")
    sentence = Forward("SE")

    t_ROOT << Literal("XR")
    t_NP_PP_J << (Literal("JKS") | Literal("JKC") | Literal("JKO") | Literal("JX"))
    t_ADJ << (((t_ROOT | t_NP) + Literal("XSA")) | Literal("VA"))
    t_VERB << (((t_ROOT | t_NP) + Literal("XSV")) | Literal("VC") | Literal("VX") | Literal("VV"))
    t_PRED << (t_ADJ | t_VERB)
    t_ADV << (Literal("MA") | (t_NP + Literal("JKM")))
    t_DET << ((t_CLAUSE + Literal("ETD")) | (t_NP + optional(Literal("JKG"))) | Literal("MD"))
    t_NOUN << (Literal("N") | (t_PP + Literal("ETN")) | ((t_ROOT | t_NP) + Literal("XSN")))
    t_NP << ((star(t_DET) + t_NOUN) | (t_NP + Literal("JC") + t_NP))
    t_PP << (star(t_ADV) + t_PRED + star(Literal("EP")))

    t_CLAUSE_NP = optional(t_NP + optional(t_NP_PP_J)).set_name("CL_NP")
    t_CLAUSE << (t_CLAUSE_NP + t_CLAUSE_NP + t_PP)

    sentence << (star((t_CLAUSE + Literal("EC")).set_name("CL+EC")) + t_CLAUSE + Literal("EF") + optional(Literal("SF")))

    return sentence

def main():

    kor_sent = ruleset4()

    parser = EarleyParser(kor_sent)
    trees = parser.parse(["N", "JKS", "VA", "ETD", "N", "JKO", "VV", "EP", "EF", "SF"], kor_sent, debug=True)

    for tree in trees:
        print(tree)
        tree.show()

if __name__ == "__main__":
    main()