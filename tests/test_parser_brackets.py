import utils.parsing.parser as parser


def render(source: str) -> str:
    return parser.render_as_markdown(parser.parse(source))


def test_double_left_bracket_block_not_link():
    source = "blah [[stuff goes here] more blah"
    rendered = render(source)

    assert "<a " not in rendered
    assert "[stuff goes here]" in rendered


def test_simple_url_bracket_still_links():
    rendered = render("[https://example.com]")
    assert "[https://example.com](https://example.com)" in rendered


def test_numeric_bracket_still_renders_superscript():
    rendered = render("See [1] for details")
    assert "<sup>[1]</sup>" in rendered


def test_aliased_local_link_handles_parentheses():
    source = "((parens (blah) inside|alias (demo)))"
    nodes = parser.parse(source)

    aliased_links = [n for n in nodes if isinstance(n, parser.AliasedLocalLinkNode)]
    assert len(aliased_links) == 1

    node = aliased_links[0]
    assert node.page == "parens (blah) inside"
    assert node.display_text == "alias (demo)"

    rendered = parser.render_as_markdown(nodes)
    assert "[alias (demo)]" in rendered


def test_multiple_aliased_links_same_line():
    source = "((First topic (intro)|Alias 1)), ~hs~ ((Second topic|Alias 2))"
    nodes = parser.parse(source)

    alias_nodes = [n for n in nodes if isinstance(n, parser.AliasedLocalLinkNode)]
    assert len(alias_nodes) == 2
    assert alias_nodes[0].display_text == "Alias 1"
    assert alias_nodes[1].display_text == "Alias 2"


def test_table_cells_ignore_aliased_link_pipes():
    source = "||((Overview Diabetes and vitamin D | Type 2 Diabetes))|8.0%|2||"
    nodes = parser.parse(source)

    table_nodes = [n for n in nodes if isinstance(n, parser.TableNode)]
    assert len(table_nodes) == 1

    row = table_nodes[0].children[0]
    assert len(row.children) == 3

    first_cell_children = row.children[0].children
    assert any(isinstance(child, parser.AliasedLocalLinkNode) for child in first_cell_children)

    rendered = parser.render_as_markdown(nodes)
    assert "| --- | --- | --- |" in rendered
    assert "[Type 2 Diabetes]" in rendered
