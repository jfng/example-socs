# SPDX-License-Identifier: BSD-2-Clause

import os
import unittest
import subprocess


class TestRtlil(unittest.TestCase):
    def test_build_runs(self):
        project_path = os.path.dirname(os.path.dirname(__file__))
        subprocess.check_call(["make", "-C", project_path, "silicon-rtlil"])
        assert os.path.exists(project_path + "/build/my_design.il")
