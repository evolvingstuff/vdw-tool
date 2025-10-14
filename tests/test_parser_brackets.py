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
