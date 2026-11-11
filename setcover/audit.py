"""Auditoria independiente: reabre originales y suma cobertura/costos sin usar el solver."""
import csv
from decimal import Decimal
from pathlib import Path
from openpyxl import load_workbook
from .data_io import DataError, sha256

def audit_originals(csv_path, excel_path, selection, reported_cost, expected_hashes=None):
    """Regla especifica autorizada: CSV ordenado 0..n-1, Excel ordenado 1..n."""
    with Path(csv_path).open(encoding='utf-8-sig', newline='') as stream:
        rows = list(csv.reader(stream, delimiter=','))
    n = len(selection)
    if rows[0] != [str(j) for j in range(n)] or len(rows) - 1 != 500 or n != 500:
        raise DataError('Auditoria original: forma/orden CSV diferente del supuesto validado.')
    if any(len(row) != n or any(cell not in ('0', '1') for cell in row) for row in rows[1:]):
        raise DataError('Auditoria original: matriz no binaria o irregular.')
    if any(bit not in (0, 1) for bit in selection):
        raise DataError('Auditoria original: seleccion no binaria.')
    book = load_workbook(excel_path, read_only=True, data_only=True)
    try:
        values = list(book['Hoja1'].values)
    finally:
        book.close()
    if len(values) != 2 or list(values[0][1:]) != list(range(1,n+1)) or len(values[1]) != n+1:
        raise DataError('Auditoria original: IDs/orden Excel diferentes del supuesto validado.')
    counts = [sum(int(cell)*bit for cell,bit in zip(row,selection)) for row in rows[1:]]
    value = sum((Decimal(str(cost))*bit for cost,bit in zip(values[1][1:],selection)), Decimal(0))
    hashes = {'csv': sha256(csv_path), 'excel': sha256(excel_path)}
    intact = expected_hashes is None or hashes == expected_hashes
    cost_ok = abs(value-Decimal(str(reported_cost))) <= Decimal('0.000001')
    return {'valida': all(v >= 1 for v in counts) and cost_ok and intact,
            'fuente': 'archivos originales reabiertos; suma Python y Decimal; sin usar matriz del solver',
            'supuesto': 'CSV j = Excel j+1; autorizado por estudiante, no confirmado por profesor',
            'clientes_cubiertos': sum(v >= 1 for v in counts), 'total_clientes': len(counts),
            'costo_recalculado_decimal': str(value), 'costo_coincide': cost_ok,
            'hashes_originales': hashes, 'originales_intactos': intact,
            'cobertura_por_cliente': counts,
            'costos_seleccionados': [{'etiqueta_csv': j, 'id_excel': j+1, 'costo_original': str(values[1][j+1])}
                                    for j,bit in enumerate(selection) if bit]}
