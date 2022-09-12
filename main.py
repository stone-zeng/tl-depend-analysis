import json
import re
import sys


def get_packages():
    TLPDB_PATH = 'tlpdb/texlive.tlpdb'
    with open(TLPDB_PATH, 'r', encoding='utf-8') as fp:
        items = fp.read().strip().split('\n\n')

    packages = {}
    for item in items[:200]:
        lines = item.split('\n')
        _, name = lines[0].split()
        if not name.startswith('00'):
            packages[name] = _parse_item(lines)

    with open('tl-packages.json', 'w', encoding='utf-8') as fp:
        json.dump(packages, fp, indent=2)


def _parse_item(lines: list[str]) -> dict[str]:
    res = {}
    depend = []
    runfiles = []
    runfiles_flag = False
    for line in lines:
        if line.startswith('category'):
            res['category'] = line.removeprefix('category ')
        elif line.startswith('revision'):
            res['revision'] = int(line.removeprefix('revision '))
        elif line.startswith('shortdesc'):
            res['description'] = line.removeprefix('shortdesc ')
        elif line.startswith('depend'):
            depend.append(line.removeprefix('depend '))

        if depend:
            res['depend'] = depend

        if line.startswith('runfiles'):
            runfiles_flag = True
        elif runfiles_flag:
            if line.startswith(' '):
                runfiles.append(line.strip())
            else:
                runfiles_flag = False

        if runfiles:
            res['runfiles'] = runfiles

    return res


class State:
    def __init__(self):
        self.stack = ''
        self.braces_count = 0
        self.braces_open = False
        self.brackets_count = 0
        self.brackets_open = False

    def __repr__(self) -> str:
        return ', '.join([
            f'stack = "{self.stack}"',
            f'braces_count = {self.braces_count}',
            f'braces_open = {self.braces_open}',
            f'brackets_count = {self.brackets_count}',
            f'brackets_open = {self.brackets_open}',
        ])

    def update(self, line: str):
        self.stack += line
        for c in line:
            match c:
                case '{':
                    self.braces_count += 1
                    self.braces_open = True
                case '}':
                    self.braces_count -= 1
                case '[':
                    self.brackets_count += 1
                    self.brackets_open = True
                case ']':
                    self.brackets_count -= 1
                    self.brackets_open = False

    def is_braces_closed(self):
        return self.braces_count == 0 and self.braces_open and not self.brackets_open

    def reset(self):
        self.stack = ''
        self.braces_count = 0
        self.braces_open = False
        self.brackets_count = 0
        self.brackets_open = False


def find_dependencies(path: str) -> set[str]:
    dep: set[str] = set()
    try:
        with open(path, 'r', encoding='utf-8') as fp:
            state = State()
            for line in fp:
                dep.update(_parse_line(line, state))
    except UnicodeDecodeError as e:
        print(f'{path}:', e, file=sys.stderr)
        with open(path, 'r', encoding='cp1252') as fp:
            state = State()
            for line in fp:
                dep.update(_parse_line(line, state))
    return dep


CLASS_PATTERN = re.compile(r'''
    \\(?:LoadClass|documentclass)\s*
    (?:\[.*\]\s*)?
    \{\s*(.+?)\s*\}
''', re.VERBOSE)

PACKAGE_PATTERN = re.compile(r'''
    \\(?:RequirePackage|RequirePackageWithOptions|usepackage)\s*
    (?:\[.*\]\s*)?
    \{\s*(.+?)\s*\}
''', re.VERBOSE)


def _parse_line(line: str, state: State) -> list[str]:
    # Skip the comments
    if line.startswith('%'):
        return []

    if match := re.findall(r'\\input\b', line):
        print('=>', line.strip(), [match])

    if state.stack == '':
        # Classes
        # - \LoadClass[...]{class}
        # - \documentclass[...]{class}
        if match := re.findall(CLASS_PATTERN, line):
            return _parse_match(match, suffix='.cls')

        # Packages
        # - \RequirePackage[...]{package}
        # - \usepackage[...]{package}
        if match := re.findall(PACKAGE_PATTERN, line):
            return _parse_match(match, suffix='.sty')

        if line.find('\\RequirePackage') >= 0 or line.find('\\usepackage') >= 0:
            state.update(line.split('%')[0].strip())

        return []

    state.update(line.split('%')[0].strip())

    if state.is_braces_closed():
        match = re.findall(PACKAGE_PATTERN, state.stack)
        state.reset()
        return _parse_match(match, suffix='.sty')

    return []


def _parse_match(match: list[str], suffix: str) -> list[str]:
    res = []
    for m in match:
        res.extend(s.strip() + suffix for s in m.split(',') if s.find('\\') == -1)
    return res


if __name__ == '__main__':
    # get_packages()

    import random

    _files = [
        'generic/atbegshi/atbegshi.sty',
        'latex/fduthesis/fduthesis.cls',
        'latex/thuthesis/thuthesis.cls',
        'latex/biblatex/biblatex.sty',
        'latex/ctex/ctxdoc.cls',
        'latex/thmtools/thmtools.sty',
        'latex/ctex/ctex.sty',
        'latex/beamerswitch/beamerswitch.cls',
        'latex/elpres/elpres.cls',
        'latex/iscram/iscram.cls',
        'latex/bangorcsthesis/bangorcsthesis.cls',
        'latex/labbook/labbook.cls',
    ]

    with open('1.txt', 'r', encoding='utf-8') as _fp:
        _files.extend(f.strip() for f in random.choices(_fp.readlines(), k=100))

    for _i in _files:
        print(f'# {_i}')
        print(find_dependencies(f'/usr/local/texlive/2022/texmf-dist/tex/{_i}'), end='\n\n')
