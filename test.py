import unittest, git, argparse
from manim import *

from git_dummy.git_dummy import GitDummy


class TestGitDummy(unittest.TestCase):
    def test_git_dummy(self):
        """Test git dummy."""

        gs = GitDummy(argparse.Namespace())

        self.assertEqual(1, 1)


if __name__ == "__main__":
    unittest.main()
