"""Check that Word layout preserves table content while fixing wide panels."""
import importlib.util
from pathlib import Path
import pytest

from docx import Document
from docx.oxml.ns import qn

spec = importlib.util.spec_from_file_location('word_layout', Path(__file__).parents[1] / 'paper/word_layout.py')
layout = importlib.util.module_from_spec(spec)
spec.loader.exec_module(layout)


@pytest.mark.parametrize('ncol', [8, 9])
def test_wide_panel_and_data_survive_landscape_formatting(tmp_path, ncol):
    path = tmp_path / 'table.docx'
    doc = Document()
    doc.add_paragraph('Before the table')
    doc.add_paragraph('Table 2. Within-district associations')
    table = doc.add_table(rows=3, cols=ncol)
    for i, cell in enumerate(table.rows[0].cells):
        cell.text = f'Original heading {i}'
    table.cell(1, 0).text = 'B. A long panel heading across all columns'
    for i, cell in enumerate(table.rows[2].cells):
        cell.text = '2026' if i == 0 else '[−0.026, 0.223]'
    doc.add_paragraph('Notes. Column definitions and assumptions.')
    doc.add_paragraph('After the table')
    doc.save(path)
    layout.format_docx(path)
    result = Document(path)
    table = result.tables[0]
    assert [c.text for c in table.rows[2].cells] == ['2026'] + ['[−0.026, 0.223]'] * (ncol-1)
    assert table.rows[1]._tr.tc_lst[0].tcPr.gridSpan.val == ncol
    assert len(table.rows[1]._tr.tc_lst) == 1
    assert table.cell(0, ncol-1).text == 'F'
    assert [p.text for p in result.paragraphs if p.text] == [
        'Before the table', 'Table 2. Within-district associations',
        'Notes. Column definitions and assumptions.', 'After the table']
    assert [s._sectPr.find(qn('w:pgSz')).get(qn('w:orient')) for s in result.sections] == [
        'portrait', 'landscape', 'portrait']
