"""Run from the project root: .venv/bin/python drafts/csv_workflow/check_draft.py"""
import csv
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch

import numpy as np
from streamlit.testing.v1 import AppTest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from csv_store import build_result_row, save_result_csv

DRAFT = Path(__file__).with_name('app_draft.py')

class Marker:
    def __init__(self, name, index):
        self.name, self.sample_index = name, index
    def __str__(self):
        return self.name


def recording():
    return NS(
        channels=[NS(name=f'{m} RMS', units='mV', samples_per_second=10,
                     data=np.ones(7000)) for m in ['ZM', 'CS']],
        samples_per_second=10,
        event_markers=[Marker('FURROW1', 0), Marker('SMILE2', 3000), Marker('Furrow2', 3200)],
    )


def click(at, label):
    next(b for b in at.button if b.label == label).click().run()
    assert not at.exception


def start(data):
    at = AppTest.from_file(str(DRAFT)).run()
    click(at, 'Start calculation')
    return at


with tempfile.TemporaryDirectory() as directory:
    path = Path(directory) / 'results.csv'
    results = {m: {k: {'value': 2.0} for k in ['baseline', 'mvc']} for m in ['ZM', 'CS']}
    row = build_result_row('001', results, [])
    assert row['needs_manual_review'] is False and row['added_at'] == ''
    assert save_result_csv(path, row) == 'created'
    before = path.read_bytes()
    assert save_result_csv(path, row) == 'duplicate'
    assert path.read_bytes() == before
    partial = build_result_row('002', {'ZM': {'baseline': {'value': 1.0}}}, ['Missing CS channel'])
    assert partial['CS MVC'] == '' and partial['needs_manual_review']
    assert save_result_csv(path, partial) == 'appended'
    with path.open(newline='') as f:
        rows = list(csv.DictReader(f))
    assert [r['study_id'] for r in rows] == ['001', '002']
    assert rows[0]['added_at'].endswith('+00:00')
    with patch('csv_store.os.replace', side_effect=OSError('Simulated write failure')):
        before = path.read_bytes()
        try:
            save_result_csv(path, build_result_row('003', results, []))
        except OSError:
            pass
        else:
            raise AssertionError('Expected save error')
        assert path.read_bytes() == before
    assert not path.with_name('results.csv.lock').exists()
    wrong = Path(directory) / 'old.csv'
    wrong.write_text('study_id,old_column\n001,1\n')
    try:
        save_result_csv(wrong, row)
    except ValueError:
        pass
    else:
        raise AssertionError('Expected schema error')
    print('PASS: create, append, duplicate, leading zeros, timestamp, partial flag, schema and write failure.')

    file = NS(name='001.acq', size=100, type='application/octet-stream')
    data = recording()
    with patch('streamlit.file_uploader', return_value=file), patch('helpers.load_acq_file', return_value=data):
        at = start(data)
        for muscle in ['ZM', 'CS']:
            click(at, 'Continue to max')
            if muscle == 'CS':
                click(at, 'Change window')
                at.number_input[0].set_value(3.0).run()
            click(at, 'Use this window and calculate max')
            click(at, 'Continue')
        assert at.session_state.stage == 'review'
        assert not at.dataframe[0].value.iloc[0]['needs_manual_review']
        at.text_input(key='output_csv').set_value(str(Path(directory) / 'ui.csv')).run()
        click(at, 'Save results')
        assert len(at.success) == 1
        click(at, 'Save results')
        assert any('already saved' in w.value for w in at.warning)
    print('PASS: both muscles, default/manual windows, final review, real CSV save, duplicate click.')

    data = recording()
    data.event_markers = [m for m in data.event_markers if m.name != 'FURROW1']
    with patch('streamlit.file_uploader', return_value=file), patch('helpers.load_acq_file', return_value=data):
        at = start(data)
        assert at.error
        for muscle in ['ZM', 'CS']:
            click(at, 'Skip baseline and flag for manual review')
            click(at, 'Use this window and calculate max')
            click(at, 'Continue')
        row = at.dataframe[0].value.iloc[0]
        assert row['ZM baseline'] == '' and row['CS baseline'] == ''
        assert row['ZM MVC'] == 1.0 and row['CS MVC'] == 1.0
        assert row['needs_manual_review']
    print('PASS: baseline failure preserves both MVC measurements and flags the result.')

    data = recording()
    data.channels = data.channels[1:]
    data.event_markers = [m for m in data.event_markers if m.name != 'Furrow2']
    with patch('streamlit.file_uploader', return_value=file), patch('helpers.load_acq_file', return_value=data):
        at = start(data)
        click(at, 'Skip muscle and flag for manual review')
        click(at, 'Continue to max')
        assert at.error
        click(at, 'Skip MVC and flag for manual review')
        row = at.dataframe[0].value.iloc[0]
        assert row['CS baseline'] == 1.0 and row['ZM baseline'] == '' and row['CS MVC'] == ''
    print('PASS: missing muscle and missing marker still reach review with the available measurement.')

    with patch('streamlit.file_uploader', return_value=file), patch('helpers.load_acq_file', side_effect=ValueError('Bad ACQ')):
        at = AppTest.from_file(str(DRAFT)).run()
        click(at, 'Review and save flagged record')
        row = at.dataframe[0].value.iloc[0]
        assert row['needs_manual_review'] and row['ZM baseline'] == ''
        at.text_input(key='study_id_input').set_value('').run()
        assert next(b for b in at.button if b.label == 'Save results').disabled
    print('PASS: unreadable file reaches flagged review; empty ID cannot be saved.')
