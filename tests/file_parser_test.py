# ruff: noqa: E501

import os
import unittest

from file_parser import Parser


class Test(unittest.TestCase):
    def test_tex_basic(self):
        expect = {'article.cls', 'geometry.sty', 'amsmath.sty', 'amsfonts.sty', 'fontspec.sty', 'hyperref.sty', 'expl3.sty', 'natbib.sty'}
        self._test('basic.tex', expect)

    def test_tex_comments(self):
        expect = {'beamer.cls', 'geometry.sty', 'tikz.sty', 'tikz-cd.sty', 'tabularx.sty', 'tabulary.sty', 'natbib.sty'}
        self._test('comments.tex', expect)

    def test_tex_fonts(self):
        expect = {'lmroman10-regular.otf', 'NotoSans-Regular.ttf', 'texgyrecursor-regular.otf', 'IBMPlexSerif-Bold.otf', 'XITSMath-Regular.otf'}
        self._test('fonts.tex', expect)

    def test_lua(self):
        expect = {'module-1.lua', 'module-7.lua', 'module-8.lua'}
        self._test('basic.lua', expect)

    def _test(self, file: str, expect: set[str]):
        path = os.path.join(os.path.dirname(__file__), 'test-data', file)
        parser = Parser(path)
        parser.parse()
        self.assertSetEqual(parser.depend, expect)


if __name__ == '__main__':
    unittest.main()
