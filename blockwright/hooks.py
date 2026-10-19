"""Hooks: Python functions for constructs a description cannot express.

A statement rule `{ hook = "name" }` calls `name(builder, node, rule)`, found
here or in the file a description names with `hooks = "file.py"`. It returns
a list of IR items (blockwright/model.py) or None to fall back to the rule's
`kind`, or to a plain process block when the rule has none. The builder
offers what a hook usually needs: builder.t(node) for the text of a node,
builder.find(node, path), builder.block(node) and builder.stmt(node) to
build nested statements, builder.L(key) for chart words.
"""
