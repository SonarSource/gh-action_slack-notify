import io
import os
import unittest
from unittest.mock import MagicMock
from unittest.mock import mock_open
from unittest.mock import patch

from github import Repository

from src.main import get_repo
from src.main import main


class TestAction(unittest.TestCase):
    @patch.dict(os.environ, {"GITHUB_EVENT": "check_run",
                             "GITHUB_ENV": "/tmp/test_env"})
    @patch("builtins.open", new_callable=mock_open)
    def test_check_run_event(self, mock_file):
        main()
        mock_file.assert_called_once_with("/tmp/test_env", 'a')
        mock_file().write.assert_called_once_with("event_type=check_run\n")

    @patch.dict(os.environ, {"GITHUB_EVENT": "check_suite",
                             "GITHUB_CHECK_SUITE_ID": "123",
                             "GITHUB_TOKEN": "test_token",
                             "GITHUB_ENV": "/tmp/test_env",
                             "GITHUB_REPOSITORY": "SonarSource/gh-action_slack-notify"})
    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("builtins.open", new_callable=mock_open)
    @patch("src.main.Github")
    def test_check_suite_event(self, mock_github, mock_file, mock_stdout):
        mock_repo = MagicMock()
        mock_check_suite = MagicMock()
        mock_check_run_success = MagicMock()
        mock_check_run_failure = MagicMock()
        mock_app = MagicMock()
        mock_app.name = "TestApp"

        mock_check_run_success.conclusion = "success"
        mock_check_run_failure.conclusion = "failure"
        mock_check_run_failure.app = mock_app
        mock_check_run_failure.head_sha = "test_sha"

        mock_check_suite.get_check_runs.return_value = [
            mock_check_run_success,
            mock_check_run_failure
        ]
        mock_repo.get_check_suite.return_value = mock_check_suite
        mock_github.return_value.get_repo.return_value = mock_repo

        main()

        self.assertEqual(mock_stdout.getvalue(
        ), "Retrieving failed check runs for check suite ID: 123\n")
        self.assertEqual(mock_file().write.call_count, 3)
        calls = mock_file().write.call_args_list
        print(calls)
        self.assertEqual(calls[0][0][0], "app_name=TestApp\n")
        self.assertEqual(calls[1][0][0], "conclusion=failure\n")
        self.assertEqual(calls[2][0][0], "head_sha=test_sha\n")

    @patch.dict(os.environ, {"GITHUB_TOKEN": "test_token"})
    @patch("src.main.Github")
    def test_get_repo(self, mock_github):
        mock_repo = MagicMock(spec=Repository)
        mock_github.return_value.get_repo.return_value = mock_repo
        repo = get_repo("SonarSource/gh-action_slack-notify")
        self.assertEqual(repo, mock_repo)
        mock_github.return_value.get_repo.assert_called_once_with(
            "SonarSource/gh-action_slack-notify")
