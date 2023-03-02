import json
import os
import subprocess
import sys

from file_parser import Parser


TLPDB_PATH = 'tlpdb/texlive.tlpdb'
TL_PACKAGES_PATH = 'data/tl-packages.json'
TL_FILES_PATH = 'data/tl-files-nofonts.csv'
TL_DEPENDENCIES_PATH = 'data/tl-dependencies.json'

TEXMFDIST_PATH = subprocess.run(
    ['kpsewhich', '-var-value', 'TEXMFDIST'],
    capture_output=True, check=True).stdout.decode().strip()
# TEXMFDIST_PATH = '/usr/local/texlive/2023/texmf-dist'


def get_packages():
    with open(TLPDB_PATH, 'r', encoding='utf-8') as fp:
        items = fp.read().strip().split('\n\n')

    packages: list[dict[str, str | list[str]]] = []
    for item in items:
        lines = item.split('\n')
        _, name = lines[0].split()
        if not name.startswith('00') and '.' not in name:
            packages.append({'name': name} | _parse_item(lines))

    with open(TL_PACKAGES_PATH, 'w', encoding='utf-8') as fp:
        json.dump(packages, fp, indent=2)

    files: list[str] = []
    for item in packages:
        name = item['name']
        if name.endswith('-dev'):  # type: ignore
            print('Skip dev package: ', name, file=sys.stderr)
            continue
        for file in item.get('runfiles', []):
            try:
                prefix, path = file.split('/', maxsplit=1)
            except ValueError:
                continue
            if prefix in ('RELOC', 'texmf-dist') and not path.startswith('fonts'):
                files.append(f'{os.path.basename(path)},{name}\n')
    files.sort()

    with open(TL_FILES_PATH, 'w', encoding='utf-8') as fp:
        fp.writelines(files)


def _parse_item(lines: list[str]):
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


def main():
    with open(TL_PACKAGES_PATH, 'r', encoding='utf-8') as fp:
        packages: list[dict] = json.load(fp)

    with open(TL_FILES_PATH, 'r', encoding='utf-8') as fp:
        files_mapping = {}
        for line in fp.readlines():
            name, pkg = line.split(',')
            files_mapping[name] = pkg.strip()

    dependencies = []
    for package in packages:
        depend = set()
        for runfile in package.get('runfiles', []):
            try:
                prefix, path = runfile.split('/', maxsplit=1)
            except ValueError:
                continue
            if prefix in ('RELOC', 'texmf-dist') and not path.startswith('fonts'):
                fullpath = os.path.join(TEXMFDIST_PATH, path)
                parser = Parser(fullpath)
                parser.parse()
                if parser.dep:
                    depend.update(files_mapping[d] for d in parser.dep if d in files_mapping)
        dependencies.append({
            'name': package['name'],
            'tl-depend': package.get('depend', []),
            'depend': sorted(depend),
        })
        with open(TL_DEPENDENCIES_PATH, 'w', encoding='utf-8') as fp:
            json.dump(dependencies, fp, indent=2)


if __name__ == '__main__':
    # get_packages()
    main()
