import os
import unittest
from unittest.mock import mock_open
from unittest.mock import patch

from src.main import main


class TestAction(unittest.TestCase):
    @patch("builtins.open", new_callable=mock_open)
    @patch.dict(os.environ, {"GITHUB_EVENT": "check_run",
                             "GITHUB_ENV": "/tmp/test_env"})
    def test_check_run_event(self, mock_file):
        main()
        mock_file.assert_called_once_with("/tmp/test_env", 'a')
        mock_file().write.assert_called_once_with("event_type=check_run\n")
