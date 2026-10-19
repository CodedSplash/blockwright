from blockwright import model as M


def assert_as_decision(builder, node, rule):
    cond = builder.t(builder.named(node)[0])
    fail = M.Simple(M.TERMINATOR, builder.L("exception_bare"), terminal=True)
    return [M.If(cond, M.Seq([]), M.Seq([fail]))]
