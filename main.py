import dataclasses
import json
import os
import subprocess
import sys
from typing import Any

from file_parser import Parser


TLPDB_PATH = 'data/texlive.tlpdb'
TL_DEPENDENCIES_PATH = 'data/tl-dependencies.json'

TEXMFDIST_PATH = subprocess.run(
    ['kpsewhich', '-var-value', 'TEXMFDIST'],
    capture_output=True, check=True).stdout.decode().strip()
# TEXMFDIST_PATH = '/usr/local/texlive/2023/texmf-dist'


@dataclasses.dataclass
class Package:
    name: str
    category: str
    revision: int
    tl_depend: list[str]
    depend: list[str]
    runfiles: list[str]


class PackageEncoder(json.JSONEncoder):

    def default(self, o):
        if isinstance(o, Package):
            return {
                'name': o.name,
                'depend': o.depend,
                'tl_depend': o.tl_depend,
            }
            # return dataclasses.asdict(o)
        return json.JSONEncoder.default(self, o)


class TLDependencies:

    def __init__(self):
        self.packages: list[Package] = []
        self.file_mappings: dict[str, str] = {}

    def parse_tlpdb(self):
        with open(TLPDB_PATH, 'r', encoding='utf-8') as fp:
            items = fp.read().strip().split('\n\n')
        for item in items:
            lines = item.split('\n')
            _, name = lines[0].split()
            if not name.startswith('00') and '.' not in name:
                self.packages.append(Package(name=name, depend=[], **self._parse_tlpdb_item(lines)))

    @staticmethod
    def _parse_tlpdb_item(lines: list[str]):
        package: dict[str, Any] = {
            'tl_depend': [],
            'runfiles': [],
        }
        runfiles_flag = False
        for line in lines:
            key, *value = line.strip().split(maxsplit=1)
            value = value[0] if value else None
            match key:
                case 'category':
                    package['category'] = value
                case 'revision':
                    package['revision'] = int(value) if value else -1
                case 'depend':
                    package['tl_depend'].append(value)
                case 'runfiles':
                    runfiles_flag = True
                case _ if runfiles_flag:
                    if line.startswith(' '):
                        package['runfiles'].append(line.strip())
                    else:
                        runfiles_flag = False
        return package

    def get_file_mappings(self):
        for package in self.packages:
            if package.name.endswith('-dev'):
                print('Skip dev package:', package.name, file=sys.stderr)
                continue
            for file in package.runfiles:
                if file.startswith('RELOC') or file.startswith('texmf-dist'):
                    _, path = file.split('/', maxsplit=1)
                    if path.startswith('fonts'):
                        continue
                    if (name := os.path.basename(path)) in self.file_mappings:
                        print('Duplicate file:', file, file=sys.stderr)
                    else:
                        self.file_mappings[name] = package.name

    def get_dependencies(self):
        for package in self.packages:
            depend: set[str] = set()
            for file in package.runfiles:
                depend.update(self._get_dependencies_from_file(file))
            package.depend = sorted(depend)

    def _get_dependencies_from_file(self, file: str):
        depend: set[str] = set()
        if file.startswith('RELOC') or file.startswith('texmf-dist'):
            _, path = file.split('/', maxsplit=1)
            if path.startswith('fonts'):
                return depend
            fullpath = os.path.join(TEXMFDIST_PATH, path)
            parser = Parser(fullpath)
            parser.parse()
            for d in parser.dep:
                try:
                    depend.add(self.file_mappings[d])
                except KeyError:
                    print('Dependency not found:', d, file=sys.stderr)
        return depend


def main():
    analyzer = TLDependencies()
    analyzer.parse_tlpdb()
    analyzer.get_file_mappings()
    analyzer.get_dependencies()
    with open(TL_DEPENDENCIES_PATH, 'w', encoding='utf-8') as fp:
        json.dump(analyzer.packages, fp, cls=PackageEncoder, indent=2)


if __name__ == '__main__':
    main()
