"""Lectura estricta sin modificar ni transponer los originales."""
from dataclasses import dataclass
from pathlib import Path
import csv
import hashlib
import math
import numpy as np
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter

class DataError(ValueError):
    """Entrada invalida o interpretacion ambigua."""

class MappingRequired(DataError):
    """Las etiquetas no establecen por si solas la correspondencia."""

@dataclass
class CoverageData:
    matrix: np.ndarray
    antenna_ids: list[str]
    client_ids: list[str]
    metadata: dict

@dataclass
class CostData:
    ids: list[str]
    costs: np.ndarray
    cells: list[str]
    metadata: dict

def sha256(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def number(value, context):
    if value is None or isinstance(value, bool) or str(value).strip() == '':
        raise DataError(f'{context}: celda vacia o booleana.')
    try:
        text = str(value).strip()
        result = float(text.replace(',', '.') if ',' in text and '.' not in text else text)
    except (ValueError, TypeError) as exc:
        raise DataError(f'{context}: valor no numerico {value!r}.') from exc
    if not math.isfinite(result):
        raise DataError(f'{context}: valor no finito.')
    return result

def identifier(value):
    if value is None or str(value).strip() == '':
        raise DataError('Identificador vacio.')
    text = str(value).strip()
    try:
        v = float(text)
        if math.isfinite(v) and v.is_integer():
            return str(int(v))
    except ValueError:
        pass
    return text

def unique(values, context):
    if len(set(values)) != len(values):
        raise DataError(f'{context}: identificadores duplicados.')

def load_coverage(path, expected_shape=(500, 500)):
    path = Path(path)
    with path.open(encoding='utf-8-sig', newline='') as stream:
        sample = stream.read(65536)
        stream.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=',;\t|')
        except csv.Error as exc:
            raise DataError('No se puede determinar el separador CSV.') from exc
        rows = list(csv.reader(stream, dialect))
    if not rows or any(not r for r in rows):
        raise DataError('CSV vacio o con filas vacias.')
    widths = {len(r) for r in rows}
    if len(widths) != 1:
        raise DataError('CSV con filas de distinta longitud.')
    m, n = expected_shape
    has_header = len(rows) == m + 1
    has_index = len(rows[0]) == n + 1
    if len(rows) not in (m, m + 1) or len(rows[0]) not in (n, n + 1):
        raise DataError(f'Dimensiones CSV incompatibles con {expected_shape}: {len(rows)} x {len(rows[0])}. No se transpone.')
    header = rows[0] if has_header else None
    body = rows[1:] if has_header else rows
    antenna_ids = [identifier(v) for v in header[int(has_index):]] if header else [str(j) for j in range(n)]
    client_ids = [identifier(r[0]) for r in body] if has_index else [str(i + 1) for i in range(m)]
    unique(antenna_ids, 'Antenas CSV')
    unique(client_ids, 'Clientes CSV')
    values = [[number(v, f'CSV fila {i + 1 + int(has_header)}, columna {j + 1 + int(has_index)}')
               for j, v in enumerate(r[int(has_index):])] for i, r in enumerate(body)]
    a = np.array(values, dtype=float)
    if a.shape != expected_shape or not np.isin(a, [0, 1]).all():
        raise DataError('La matriz debe tener la forma esperada y contener exclusivamente 0/1.')
    return CoverageData(a.astype(np.int64), antenna_ids, client_ids, {
        'archivo': path.name, 'sha256': sha256(path), 'separador': dialect.delimiter,
        'encabezado': has_header, 'indice_clientes_en_archivo': has_index,
        'ids_antenas_generados': not has_header, 'orientacion': 'filas=clientes; columnas=antenas; sin transposicion',
        'filas_archivo': len(rows), 'columnas_archivo': len(rows[0]),
    })

def load_costs(path, expected_count=500, sheet=None):
    path = Path(path)
    book = load_workbook(path, read_only=True, data_only=True)
    formula_book = load_workbook(path, read_only=True, data_only=False)
    try:
        candidates = []
        for ws in book:
            if sheet is not None and ws.title != sheet:
                continue
            rows = list(ws.values)
            if len(rows) == 2 and len(rows[0]) == expected_count + 1:
                if str(rows[0][0]).strip().lower() == 'conjunto' and str(rows[1][0]).strip().lower() == 'costo':
                    candidates.append((ws, list(rows[0][1:]), list(rows[1][1:]),
                                       [f'{get_column_letter(j+2)}2' for j in range(expected_count)], 'horizontal'))
            if len(rows) == expected_count + 1 and len(rows[0]) == 2:
                if [str(x).strip().lower() for x in rows[0]] == ['conjunto', 'costo']:
                    candidates.append((ws, [r[0] for r in rows[1:]], [r[1] for r in rows[1:]],
                                       [f'B{i+2}' for i in range(expected_count)], 'vertical'))
        if len(candidates) != 1:
            raise DataError('Excel: se requiere una unica tabla reconocible Conjunto/Costo, horizontal o vertical; indique hoja si hay varias.')
        ws, raw_ids, raw_costs, cells, layout = candidates[0]
        ids = [identifier(v) for v in raw_ids]
        unique(ids, 'Antenas Excel')
        costs = np.array([number(v, f'{ws.title}!{cell}') for v, cell in zip(raw_costs, cells)], dtype=float)
        if (costs < 0).any():
            raise DataError('Los costos deben ser no negativos.')
        formula_cells = [cell.coordinate for row in formula_book[ws.title] for cell in row if cell.data_type == 'f']
        return CostData(ids, costs, cells, {
            'archivo': path.name, 'sha256': sha256(path), 'hoja': ws.title,
            'disposicion': layout, 'etiquetas': ['Conjunto', 'Costo'],
            'celdas_con_formula': formula_cells,
            'lectura_formulas': 'valores almacenados por Excel; openpyxl no recalcula formulas',
        })
    finally:
        book.close()
        formula_book.close()

def align_costs(coverage, costs, mapping=None):
    """La regla ordinal requiere una decision explicita documentada; no demuestra identidad fisica."""
    ids = coverage.antenna_ids
    if set(ids) == set(costs.ids):
        target_ids = ids
        rule = 'igualdad de etiquetas; reordenacion por ID'
    elif mapping == 'ordinal-0-1':
        n = len(ids)
        if set(ids) != {str(j) for j in range(n)} or set(costs.ids) != {str(j+1) for j in range(n)}:
            raise DataError('La regla ordinal-0-1 exige los conjuntos completos 0..n-1 y 1..n.')
        target_ids = [str(int(j) + 1) for j in ids]
        rule = 'regla explicita ordinal-0-1: ID Excel = etiqueta CSV + 1'
    else:
        raise MappingRequired('Etiquetas diferentes: confirmar la correspondencia antes de alinear costos. No se aplica desplazamiento automatico.')
    positions = {label: k for k, label in enumerate(costs.ids)}
    mapping_rows = [{'posicion_vector': j, 'etiqueta_csv': label, 'id_excel': target,
                     'celda_excel': costs.cells[positions[target]], 'costo': float(costs.costs[positions[target]])}
                    for j, (label, target) in enumerate(zip(ids, target_ids))]
    return np.array([r['costo'] for r in mapping_rows]), mapping_rows, rule
