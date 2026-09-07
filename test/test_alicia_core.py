"""
Test Suite for Alicia Assistant Core Components
"""

import os
import sys
import unittest
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import settings
from config.theme import get_theme, load_stylesheet
from database.manager import db
from src.core.utils import crosspath, crossplatform
from src.core.cmd.system import system
from src.core.cmd.action import execute_command
from src.core.voice.fuzz import matches_wake_word, similarity_ratio
from src.core.voice.vad import vad


class TestAliciaCore(unittest.TestCase):

    def test_01_settings_and_paths(self):
        self.assertIsNotNone(settings.root_dir)
        self.assertTrue(settings.database_dir.exists())
        self.assertIn("alicia", settings.voice.wake_words)

    def test_02_theme(self):
        theme = get_theme("dark_neon")
        self.assertIn("accent_cyan", theme)
        self.assertIn("bg_primary", theme)

    def test_03_database_manager(self):
        user = db.get_user_name()
        self.assertEqual(user, "Kalpesh")
        note_res = db.add_note("Test note for Alicia test suite")
        self.assertIn("saved", note_res.lower())
        notes = db.list_notes()
        self.assertTrue(len(notes) > 0)
        self.assertEqual(notes[-1]["content"], "Test note for Alicia test suite")

    def test_04_crossplatform_and_paths(self):
        root = crosspath.get_project_root()
        self.assertTrue(root.exists())
        os_name = crossplatform.get_os_name()
        self.assertIn(os_name, ["linux", "windows", "darwin"])

    def test_05_system_commands(self):
        t = system.get_time()
        self.assertTrue(len(t) > 0)
        d = system.get_date()
        self.assertTrue(len(d) > 0)
        u = system.uptime()
        self.assertTrue(len(u) > 0)
        cpu = system.cpu_usage(interval=0.1)
        self.assertIsInstance(cpu, float)
        ram = system.ram_usage()
        self.assertIn("percent", ram)
        bat = system.get_battery()
        self.assertIn("present", bat)

    def test_06_action_dispatcher(self):
        # Time command
        res_time = execute_command("what time is it")
        self.assertIn("currently", res_time.lower())

        # Date command
        res_date = execute_command("what day is it")
        self.assertIn("today is", res_date.lower())

        # System stats
        res_stats = execute_command("cpu status")
        self.assertIn("cpu usage", res_stats.lower())

        # Notes list
        res_notes = execute_command("show notes")
        self.assertIn("note", res_notes.lower())

    def test_07_fuzzy_matching(self):
        matched, word = matches_wake_word("hey alicia can you help me")
        self.assertTrue(matched)
        matched_typo, word_typo = matches_wake_word("alisa what time is it")
        self.assertTrue(matched_typo)
        not_matched, _ = matches_wake_word("play some music on the speaker")
        self.assertFalse(not_matched)

    def test_08_vad_rms(self):
        import numpy as np
        silence = np.zeros(1600, dtype=np.float32)
        self.assertEqual(vad.calculate_rms(silence), 0.0)
        self.assertFalse(vad.is_speech(silence))

        tone = np.sin(np.linspace(0, 100, 1600)).astype(np.float32) * 0.5
        self.assertTrue(vad.calculate_rms(tone) > 0.01)
        self.assertTrue(vad.is_speech(tone))


if __name__ == "__main__":
    unittest.main()
