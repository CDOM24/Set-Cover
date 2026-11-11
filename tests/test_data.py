"""Todas las instancias creadas aqui son SINTETICAS DE PRUEBA."""
import csv
from itertools import product
from pathlib import Path
import numpy as np
from openpyxl import Workbook
import pytest
from setcover.data_io import (CostData, CoverageData, DataError, MappingRequired,
                              align_costs, load_costs, load_coverage, sha256)
from setcover.validation import diagnose, validate_arrays
from setcover.verification import verify_solution

ROOT = Path(__file__).resolve().parents[1]

def csv_file(tmp_path, rows, delimiter=','):
    path = tmp_path / 'prueba.csv'
    with path.open('w', encoding='utf-8-sig', newline='') as stream:
        csv.writer(stream, delimiter=delimiter).writerows(rows)
    return path

def xlsx_file(tmp_path, rows, second_sheet=False):
    path = tmp_path / 'prueba.xlsx'
    book = Workbook()
    sheet = book.active
    sheet.title = 'Prueba'
    for row in rows:
        sheet.append(row)
    if second_sheet:
        other = book.create_sheet('Otra')
        for row in rows:
            other.append(row)
    book.save(path)
    book.close()
    return path

@pytest.mark.parametrize('sep', [',', ';', '\t', '|'])
def test_csv_separators_header_index(tmp_path, sep):
    path = csv_file(tmp_path, [['cliente', '0', '1'], ['c1', '1', '0'], ['c2', '0', '1']], sep)
    data = load_coverage(path, (2, 2))
    assert data.antenna_ids == ['0', '1']
    assert data.client_ids == ['c1', 'c2']
    assert data.metadata['separador'] == sep
    assert data.metadata['indice_clientes_en_archivo']
    np.testing.assert_array_equal(data.matrix, np.eye(2))

def test_csv_without_header(tmp_path):
    data = load_coverage(csv_file(tmp_path, [[1, 0], [0, 1]]), (2, 2))
    assert not data.metadata['encabezado']
    assert data.metadata['ids_antenas_generados']

def test_csv_decimal_comma(tmp_path):
    path = csv_file(tmp_path, [['0', '1'], ['1,0', '0,0'], ['0,0', '1,0']], ';')
    np.testing.assert_array_equal(load_coverage(path, (2, 2)).matrix, np.eye(2))

@pytest.mark.parametrize('rows', [
    [['0', '1'], [1, ''], [0, 1]],
    [['0', '1'], [1, 2], [0, 1]],
    [['0', '1'], [1, 'NaN'], [0, 1]],
    [['0', '1'], [1, 'inf'], [0, 1]],
    [['0', '1'], [1], [0, 1]],
    [['0', '0'], [1, 0], [0, 1]],
    [['cliente', '0', '1'], ['c1', 1, 0], ['c1', 0, 1]],
    [[1, 0, 1], [0, 1, 0], [1, 0, 1], [0, 1, 0]],
])
def test_bad_csv_rejected(tmp_path, rows):
    with pytest.raises(DataError):
        load_coverage(csv_file(tmp_path, rows), (2, 2))

@pytest.mark.parametrize('rows,layout', [
    ([['Conjunto', 1, 2], ['Costo ', 9, 4]], 'horizontal'),
    ([['Conjunto', 'Costo'], [1, 9], [2, 4]], 'vertical'),
])
def test_excel_layouts(tmp_path, rows, layout):
    data = load_costs(xlsx_file(tmp_path, rows), 2)
    assert data.ids == ['1', '2']
    assert data.costs.tolist() == [9, 4]
    assert data.metadata['disposicion'] == layout

@pytest.mark.parametrize('rows', [
    [['Conjunto', 1, 2], ['Costo', 3, -1]],
    [['Conjunto', 1, 2], ['Costo', 3, None]],
    [['Conjunto', 1, 2], ['Costo', 3, 'NaN']],
    [['Conjunto', 1, 1], ['Costo', 3, 2]],
    [['Conjunto', 1, 2], ['Costo', 3, '=1+1']],
    [['Conjunto', 1, 2], ['Precio no reconocido', 3, 2]],
    [['Conjunto', 1, 2, 3], ['Costo', 3, 2, 1]],
])
def test_bad_excel_rejected(tmp_path, rows):
    with pytest.raises(DataError):
        load_costs(xlsx_file(tmp_path, rows), 2)

def test_ambiguous_sheets(tmp_path):
    path = xlsx_file(tmp_path, [['Conjunto', 1, 2], ['Costo', 3, 2]], True)
    with pytest.raises(DataError):
        load_costs(path, 2)
    assert load_costs(path, 2, sheet='Otra').metadata['hoja'] == 'Otra'

def test_zero_cost_allowed(tmp_path):
    data = load_costs(xlsx_file(tmp_path, [['Conjunto', 1, 2], ['Costo', 0, 2]]), 2)
    assert data.costs.min() == 0

def test_explicit_mapping_and_reorder():
    coverage = CoverageData(np.eye(3), ['2', '0', '1'], ['a', 'b', 'c'], {})
    costs = CostData(['2', '3', '1'], np.array([20, 30, 10]), ['B2', 'C2', 'D2'], {})
    with pytest.raises(MappingRequired):
        align_costs(coverage, costs)
    aligned, rows, _ = align_costs(coverage, costs, 'ordinal-0-1')
    assert aligned.tolist() == [30, 10, 20]
    assert rows[0]['id_excel'] == '3'
    assert rows[0]['celda_excel'] == 'C2'
    costs.ids = ['a', 'b', 'c']
    with pytest.raises(DataError):
        align_costs(coverage, costs, 'ordinal-0-1')

def test_same_ids_mapping():
    coverage = CoverageData(np.eye(2), ['b', 'a'], ['1', '2'], {})
    costs = CostData(['a', 'b'], np.array([4, 7]), ['B2', 'C2'], {})
    assert align_costs(coverage, costs)[0].tolist() == [7, 4]

def test_infeasible_and_duplicate_diagnostics():
    coverage = CoverageData(np.array([[1, 1, 0], [1, 1, 0], [0, 0, 0]]), ['a', 'b', 'c'], ['1', '2', '3'], {})
    costs = CostData(['a', 'b', 'c'], np.array([1, 1, 2]), ['B2', 'C2', 'D2'], {})
    result = diagnose(coverage, costs)
    assert not result['factibilidad_cobertura']
    assert result['clientes_sin_cobertura'] == ['3']
    assert result['antenas_sin_cobertura'] == ['c']
    assert result['filas_duplicadas'] == [['1', '2']]
    assert result['columnas_duplicadas'] == [['a', 'b']]

@pytest.mark.parametrize('a,c', [([[1, 2]], [1, 2]), ([[1, 0]], [1]), ([[1, 0]], [1, -1]), ([[1, 0]], [1, float('inf')])])
def test_arrays_invalid(a, c):
    with pytest.raises(DataError):
        validate_arrays(a, c)

def test_toy_known_optimum_only_synthetic():
    # Ocho selecciones; ninguna antena individual cubre los tres clientes.
    a = np.array([[1, 0, 1], [1, 1, 0], [0, 1, 1]])
    c = np.array([2, 3, 2])
    feasible = [(float(c @ x), x) for x in product([0, 1], repeat=3) if (a @ x >= 1).all()]
    assert min(feasible) == (4.0, (1, 0, 1))
    assert verify_solution(a, c, [1, 0, 1], 4)['valida']
    assert not verify_solution(a, c, [1, 0, 0], 2)['valida']
    assert not verify_solution(a, c, [1, 0, 1], 99)['valida']

@pytest.mark.parametrize('x', [[1, 0], [0.5, 0, 1], [1, float('nan'), 0]])
def test_invalid_selections(x):
    with pytest.raises(DataError):
        verify_solution(np.eye(3), [1, 2, 3], x)

def test_no_integer_overflow_at_500():
    result = verify_solution(np.ones((500, 500), dtype=np.uint8), np.ones(500), np.ones(500), 500)
    assert result['valida'] and result['clientes_cubiertos'] == 500

def test_real_originals_integrity_and_import():
    data_dir = ROOT / 'datos'
    a = load_coverage(data_dir / 'set_cover_500x500.csv')
    c = load_costs(data_dir / 'Costo_S.xlsx')
    assert a.matrix.shape == (500, 500)
    assert c.costs.shape == (500,)
    from setcover.catalog import verify_manifest
    assert verify_manifest(ROOT) > 0
    with pytest.raises(MappingRequired):
        align_costs(a, c)


def test_real_positional_assumption_matches_original_excel():
    # Comprueba la consistencia estructural del supuesto autorizado, no su identidad fisica.
    from openpyxl import load_workbook
    a = load_coverage(ROOT / 'datos/set_cover_500x500.csv')
    c = load_costs(ROOT / 'datos/Costo_S.xlsx')
    assert a.antenna_ids == [str(j) for j in range(500)]
    assert c.ids == [str(j + 1) for j in range(500)]
    aligned, mapping, _ = align_costs(a, c, 'ordinal-0-1')
    book = load_workbook(ROOT / 'datos/Costo_S.xlsx', read_only=True, data_only=True)
    try:
        rows = list(book['Hoja1'].values)
        assert list(rows[0][1:]) == list(range(1, 501))
        np.testing.assert_array_equal(aligned, rows[1][1:])
        for j, entry in enumerate(mapping):
            assert entry['posicion_vector'] == j
            assert entry['etiqueta_csv'] == str(j)
            assert entry['id_excel'] == str(j + 1)
            assert entry['costo'] == rows[1][j + 1]
    finally:
        book.close()
