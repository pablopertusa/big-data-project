"""Descarga el cuadro de festivos laborales de 2023 del BOE oficial."""

import argparse
import csv
from pathlib import Path
from urllib.request import urlopen
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[1]
URL = 'https://www.boe.es/diario_boe/xml.php?id=BOE-A-2022-16755'
DESTINATION = ROOT / 'data/boe/calendario_festivos_2023.csv'


def calendar_rows(document):
    def text(cell):
        return ' '.join(''.join(cell.itertext()).split())

    for table in document.findall('.//table'):
        headings = table.findall('./thead/tr')
        if not headings or text(headings[0][0]) != 'Fecha de las fiestas':
            continue
        header = [text(headings[0][0]), *(text(cell) for cell in headings[1])]
        rows = [[text(cell) for cell in row] for row in table.findall('./tbody/tr')]
        if len(header) != 20 or not rows or any(len(row) != len(header) for row in rows):
            raise ValueError('Estructura inesperada en el calendario del BOE.')
        return [header, *rows]
    raise ValueError('No se encontró el calendario en el documento del BOE.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--force', action='store_true', help='Volver a descargar aunque el CSV ya exista.')
    args = parser.parse_args()
    if DESTINATION.is_file() and not args.force:
        print(f'Ya existe: {DESTINATION.relative_to(ROOT)}')
        return

    with urlopen(URL, timeout=60) as response:
        rows = calendar_rows(ElementTree.parse(response))
    DESTINATION.parent.mkdir(parents=True, exist_ok=True)
    temporary = DESTINATION.with_suffix('.csv.part')
    with temporary.open('w', encoding='utf-8-sig', newline='') as output:
        csv.writer(output, delimiter=';').writerows(rows)
    temporary.replace(DESTINATION)
    print(f'Descargado: {DESTINATION.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
