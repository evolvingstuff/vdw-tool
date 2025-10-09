import unittest

from utils.parsing import parser


class HtmlRenderingTests(unittest.TestCase):
    def test_inline_tiki_markup_inside_html_is_rendered_as_html(self) -> None:
        source = "<div>__Bold__ [https://example.com|Example]</div>"
        rendered = parser.render_as_markdown(parser.parse(source)).strip()
        expected = '<div><strong>Bold</strong> <a href="https://example.com">Example</a></div>'
        self.assertEqual(' '.join(rendered.split()), ' '.join(expected.split()))

    def test_standard_markdown_inside_html_is_normalized(self) -> None:
        source = "<div>**Bold** [Example](https://example.com)</div>"
        rendered = parser.render_as_markdown(parser.parse(source)).strip()
        expected = '<div><strong>Bold</strong> <a href="https://example.com">Example</a></div>'
        self.assertEqual(' '.join(rendered.split()), ' '.join(expected.split()))

    def test_html_macro_respects_inline_markup(self) -> None:
        source = "{HTML()}<div>__Bold__ [https://example.com|Example]</div>{HTML}"
        rendered = parser.render_as_markdown(parser.parse(source)).strip()
        expected = '<div><strong>Bold</strong> <a href="https://example.com">Example</a></div>'
        self.assertEqual(' '.join(rendered.split()), ' '.join(expected.split()))

    def test_whitespace_between_inline_html_fragments_is_preserved(self) -> None:
        source = "{BOX()}__Bone - Health__ category {BOX}"
        rendered = parser.render_as_markdown(parser.parse(source))
        self.assertIn("</strong> category", rendered)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
