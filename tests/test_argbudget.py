import importlib.machinery
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / 'argbudget'
loader = importlib.machinery.SourceFileLoader('argbudget', str(TOOL))
spec = importlib.util.spec_from_loader(loader.name, loader)
m = importlib.util.module_from_spec(spec)
loader.exec_module(m)


class BudgetTests(unittest.TestCase):
    def test_bytes(self):
        r = m.measure({b'A': b'abc'}, [b'tool', b''], 1000, 8)
        self.assertEqual(r['environment_bytes'], 6)
        self.assertEqual(r['argument_bytes'], 6)
        self.assertEqual(r['pointer_estimate_bytes'], 40)
        self.assertEqual(r['estimated_total_bytes'], 52)

    def test_unicode_counts_bytes(self):
        r = m.measure({b'A': 'ş'.encode()}, ['ş'.encode()], 1000, 8)
        self.assertEqual(r['argument_bytes'], 3)
        self.assertEqual(r['environment_bytes'], 5)

    def test_raw_bytes(self):
        self.assertEqual(m.read_arguments(io.BytesIO(b'\xff\0')), [b'\xff'])

    def test_empty_arguments(self):
        self.assertEqual(m.read_arguments(io.BytesIO(b'\0\0')), [b'', b''])
        self.assertEqual(m.read_arguments(io.BytesIO(b'')), [])

    def test_invalid_termination(self):
        with self.assertRaises(ValueError):
            m.read_arguments(io.BytesIO(b'x'))

    def test_bounded_input(self):
        with patch.object(m, 'MAX_INPUT', 8):
            with self.assertRaises(ValueError):
                m.read_arguments(io.BytesIO(b'x' * 9))

    def test_thresholds(self):
        self.assertEqual(m.measure({}, [b'a'*80], 100, 1)['status'], 'NEAR_LIMIT')
        self.assertEqual(m.measure({}, [b'a'*100], 100, 1)['status'], 'OVER_ESTIMATE')

    def test_names_redacted(self):
        r = m.measure({b'bad\n/path': b'PRIVATE'}, [], 1000, 8)
        self.assertEqual(r['largest_environment'][0]['name'], '[nonstandard-name-hidden]')
        self.assertNotIn('PRIVATE', json.dumps(r))

    def test_linux_individual_limit(self):
        with patch.object(sys, 'platform', 'linux'), patch.object(os, 'sysconf', return_value=4096):
            r = m.measure({}, [b'x' * 131072], 2000000, 8)
            self.assertEqual(r['status'], 'OVER_ESTIMATE')
            self.assertTrue(r['linux_string_limit_exceeded'])

    def test_cli_privacy_and_real_stdin(self):
        env = dict(os.environ, ARGBUDGET_TEST_SECRET='private-value-marker')
        p = subprocess.run([sys.executable, str(TOOL), '--stdin0', '--json', '--hide-names'],
                           input=b'/private/test-path\0\0', env=env, capture_output=True)
        self.assertEqual(p.returncode, 0)
        r = json.loads(p.stdout)
        self.assertEqual(r['argument_count'], 2)
        self.assertEqual(r['argument_bytes'], 20)
        for text in (b'private-value-marker', b'/private/test-path', b'ARGBUDGET_TEST_SECRET'):
            self.assertNotIn(text, p.stdout + p.stderr)
        self.assertFalse(r['execution_guaranteed'])

    def test_cli_invalid(self):
        p = subprocess.run([sys.executable, str(TOOL), '--stdin0'], input=b'not-null', capture_output=True)
        self.assertEqual(p.returncode, 2)
        self.assertNotIn(b'not-null', p.stderr)

    def test_cli_check(self):
        p = subprocess.run([sys.executable, str(TOOL), '--stdin0', '--check', '--json'],
                           input=b'tool\0' + b'x' * 10_000_000 + b'\0', capture_output=True)
        self.assertEqual(p.returncode, 1)
        self.assertEqual(json.loads(p.stdout)['status'], 'OVER_ESTIMATE')


if __name__ == '__main__':
    unittest.main()
