import os
import unittest
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from github import Repository
from github.NamedUser import NamedUser
from slack_sdk.errors import SlackApiError

from src.main import create_slack_attachments
from src.main import get_failed_check_runs
from src.main import get_github_user_by_id
from src.main import get_repo
from src.main import get_slack_user_by_name
from src.main import post_message


class TestAction(unittest.TestCase):
    @patch.dict(os.environ, {"GITHUB_TOKEN": "test_token"})
    @patch("src.main.Github")
    def test_get_repo(self, mock_github):
        mock_repo = MagicMock(spec=Repository)
        mock_github.return_value.get_repo.return_value = mock_repo
        repo = get_repo("SonarSource/gh-action_slack-notify")
        self.assertEqual(repo, mock_repo)
        mock_github.return_value.get_repo.assert_called_once_with(
            "SonarSource/gh-action_slack-notify")

    @patch.dict(os.environ, {"GITHUB_TOKEN": "test_token"})
    @patch("src.main.Github")
    def test_get_github_user_by_id(self, mock_github):
        mock_user = MagicMock()
        mock_github.return_value.get_user_by_id.return_value = mock_user
        user = get_github_user_by_id("123")
        self.assertEqual(user, mock_user)
        mock_github.return_value.get_user_by_id.assert_called_once_with(123)

    def test_create_slack_attachments(self):
        check_runs = [MagicMock(), MagicMock()]
        check_runs[0].conclusion = "failure"
        check_runs[1].conclusion = "success"
        attachments = create_slack_attachments(check_runs, "repo", "user")
        self.assertEqual(len(attachments), 2)

    def test_get_failed_check_runs(self):
        check_suite = MagicMock()
        check_suite.get_check_runs.return_value = [MagicMock(), MagicMock()]
        check_suite.get_check_runs()[0].conclusion = "failure"
        check_suite.get_check_runs()[1].conclusion = "success"
        failed_check_runs = get_failed_check_runs(check_suite)
        self.assertEqual(len(failed_check_runs), 1)

    def test_get_failed_check_runs_without_failed_check_runs(self):
        check_suite = MagicMock()
        check_suite.get_check_runs.return_value = [MagicMock(), MagicMock()]
        check_suite.get_check_runs()[0].conclusion = "success"
        check_suite.get_check_runs()[1].conclusion = "success"
        failed_check_runs = get_failed_check_runs(check_suite)
        self.assertEqual(len(failed_check_runs), 0)

    def test_get_failed_check_runs_with_failed_check_runs(self):
        check_suite = MagicMock()
        check_suite.get_check_runs.return_value = [MagicMock(), MagicMock()]
        check_suite.get_check_runs()[0].conclusion = "failure"
        check_suite.get_check_runs()[1].conclusion = "failure"
        failed_check_runs = get_failed_check_runs(check_suite)
        self.assertEqual(len(failed_check_runs), 2)

    @patch.dict(os.environ, {"SLACK_TOKEN": "test_token"})
    @patch("src.main.WebClient")
    def test_get_slack_user_by_name(self, mock_slack):
        mock_slack.return_value.users_list.return_value = {
            "members": [{"profile": {"first_name": "John", "last_name": "Doe"}}]}
        github_user = MagicMock(spec=NamedUser)
        github_user.name = "John Doe"
        user = get_slack_user_by_name(github_user)
        self.assertEqual(user, {'profile': {'first_name': 'John', 'last_name': 'Doe'}})

    @patch.dict(os.environ, {"SLACK_TOKEN": "test_token"})
    @patch("src.main.WebClient")
    def test_get_slack_user_by_name_not_found(self, mock_slack):
        mock_slack.return_value.users_list.return_value = {
            "members": [{"profile": {"first_name": "John", "last_name": "Doe"}}]}
        github_user = MagicMock(spec=NamedUser)
        github_user.name = "Jane Smith"
        user = get_slack_user_by_name(github_user)
        self.assertIsNone(user)

    @patch.dict(os.environ, {"SLACK_TOKEN": "test_token"})
    @patch("src.main.WebClient")
    def test_get_slack_user_by_name_api_error(self, mock_slack):
        mock_slack.return_value.users_list.side_effect = SlackApiError(
            response=MagicMock(status_code=500, data={"ok": False, "error": "internal_error"}),
            message="Slack API Error"
        )
        github_user = MagicMock(spec=NamedUser)
        github_user.name = "Jane Smith"
        with pytest.raises(SystemExit) as excinfo:
            get_slack_user_by_name(github_user)

        assert excinfo.value.code == 1

    @patch.dict(os.environ, {"SLACK_TOKEN": "test_token"})
    @patch("src.main.WebClient")
    def test_get_slack_user_by_name_ratelimit(self, mock_slack):
        mock_slack.return_value.users_list.side_effect = [SlackApiError(
            response=MagicMock(status_code=429, headers={"Retry-After": 1}),
            message="Rate limited"
        ), {"members": [{"profile": {"first_name": "John", "last_name": "Doe"}}]}]
        github_user = MagicMock(spec=NamedUser)
        github_user.name = "John Doe"
        get_slack_user_by_name(github_user)
        assert mock_slack.return_value.users_list.call_count == 2

    @patch.dict(os.environ, {"SLACK_TOKEN": "test_token"})
    @patch("src.main.WebClient")
    def test_post_message(self, mock_slack):
        mock_slack.return_value.chat_postMessage.return_value = {"ok": True}
        attachments = [{"text": "Test attachment"}]
        post_message("test_channel", attachments)
        mock_slack.return_value.chat_postMessage.assert_called_once_with(
            channel="test_channel", text="Failed check runs", attachments=attachments
        )

    @patch.dict(os.environ, {"SLACK_TOKEN": "test_token"})
    @patch("src.main.WebClient")
    def test_post_message_with_ratelimit(self, mock_slack):
        mock_slack.return_value.chat_postMessage.side_effect = [SlackApiError(
            response=MagicMock(status_code=429, headers={"Retry-After": 1}),
            message="Rate limited"
        ), {"ok": True}]
        attachments = [{"text": "Test attachment"}]
        post_message("test_channel", attachments)
        assert mock_slack.return_value.chat_postMessage.call_count == 2
        mock_slack.return_value.chat_postMessage.assert_called_with(
            channel="test_channel", text="Failed check runs", attachments=attachments
        )

        with patch('time.sleep') as mock_sleep:
            mock_slack.return_value.chat_postMessage.side_effect = [SlackApiError(
                response=MagicMock(status_code=429, headers={"Retry-After": 1}),
                message="Rate limited"
            ), {"ok": True}]
            post_message("test_channel", attachments)
            mock_sleep.assert_called_once_with(1)
