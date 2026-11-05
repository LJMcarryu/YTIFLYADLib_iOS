#!/usr/bin/env python3
import subprocess
import sys
import unittest
from pathlib import Path


class PublicContractTest(unittest.TestCase):
    def test_public_contract(self):
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            [sys.executable, str(root / "scripts/verify_public_contract.py")],
            cwd=root,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
