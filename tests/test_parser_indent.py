import unittest

from utils.parsing import parser


class ParserIndentTests(unittest.TestCase):
    def test_plus_line_within_list_becomes_nested_bullet(self) -> None:
        tiki = "* Parent\n+Child detail\n"
        rendered = parser.render_as_markdown(parser.parse(tiki))
        self.assertIn("* Parent\n  * Child detail", rendered)

    def test_multiple_plus_lines(self) -> None:
        tiki = "* Parent\n+First\n+Second\n"
        rendered = parser.render_as_markdown(parser.parse(tiki))
        self.assertIn("  * First", rendered)
        self.assertIn("  * Second", rendered)

    def test_full_magnesium_example(self) -> None:
        tiki = "There is a controversy as to which form of Magnesium is best\n*Liquid form: Magnesium Chloride has good bioavailability and a low laxative effect.\n+Can also be used topically on sore muscles\n*Pill form: Magnesium Citrate has a relatively more laxative effect than other forms\n+Avoid Magnesium Oxide - consensus = very low bio-availability (not much better than placebo)\n+Be careful that the supplement does not contain Calcium (most people need to reduce Ca intake)\n"
        rendered = parser.render_as_markdown(parser.parse(tiki)).strip()
        expected = (
            "There is a controversy as to which form of Magnesium is best\n\n"
            "* Liquid form: Magnesium Chloride has good bioavailability and a low laxative effect.\n"
            "  * Can also be used topically on sore muscles\n"
            "* Pill form: Magnesium Citrate has a relatively more laxative effect than other forms\n"
            "  * Avoid Magnesium Oxide - consensus = very low bio-availability (not much better than placebo)\n"
            "  * Be careful that the supplement does not contain Calcium (most people need to reduce Ca intake)"
        )
        self.assertEqual(rendered, expected)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
