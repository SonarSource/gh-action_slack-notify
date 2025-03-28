import logging
import os
import sys
import time
from typing import List

from github import Github
from github import GithubException
from github.CheckRun import CheckRun
from github.CheckSuite import CheckSuite
from github.NamedUser import NamedUser
from github.Repository import Repository
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


logger = logging.getLogger(__name__)


def get_repo(repository: str) -> Repository:
    logger.info(f"Getting repository: {repository}")
    g = Github(os.environ.get('GITHUB_TOKEN'))
    return g.get_repo(repository)


def get_failed_check_runs(check_suite: CheckSuite) -> List[CheckRun]:
    logger.info(f"Getting check runs for check suite ID: {check_suite.id}")
    check_runs = check_suite.get_check_runs()
    return [check_run for check_run in check_runs if check_run.conclusion == "failure"]


def get_github_user_by_id(github_actor_id: str) -> NamedUser:
    """Get the GitHub user by ID."""
    logging.info(f"Getting GitHub user by ID {github_actor_id}")
    github = Github(os.environ.get('GITHUB_TOKEN'))
    return github.get_user_by_id(int(github_actor_id))


def find_slack_user(users_list: List, first_name: str, last_name: str):
    for user in users_list:
        profile = user["profile"]
        if profile.get("first_name", "") == first_name and profile.get("last_name", "") == last_name:
            return user
    return None


def get_slack_user_by_name(github_user: NamedUser):
    """Get the Slack user for a given user name."""
    if github_user.name is None:
        return None

    first_name, last_name = github_user.name.split(' ')
    logging.info(f"Getting Slack user by name: {first_name} {last_name}")
    client = WebClient(token=os.environ.get('SLACK_TOKEN'))

    try:
        logging.info("Listing Slack users")
        users = client.users_list()
        return find_slack_user(users["members"], first_name, last_name)
    except SlackApiError as e:
        if e.response.status_code == 429:
            delay = int(e.response.headers["Retry-After"])
            logging.info(f"Rate limited. Retrying in {delay} seconds.")
            time.sleep(delay)
            users = client.users_list()
            return find_slack_user(users["members"], first_name, last_name)
        else:
            logging.error(f"Error listing Slack users: {e.response}")
            sys.exit(1)


def create_slack_attachments(check_runs: List[CheckRun],
                             repository_name: str,
                             slack_user_id: str) -> List:
    """Create Slack attachments for failed check runs and a given repository
    and a given Slack user."""
    attachments = []
    for check_run in check_runs:
        attachment = {
            "color": "danger",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*{check_run.app.name}* - <{check_run.details_url}|{check_run.name}> {check_run.conclusion}  in *{repository_name}*"  # noqa E501
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"Branch: *{check_run.check_suite.head_branch}*\nCommit: *{check_run.head_sha}*\nActor: <@{slack_user_id}>"  # noqa E501
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "image",
                            "image_url": f"{check_run.app.owner.avatar_url}",
                            "alt_text": "Icon"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"<{check_run.details_url}|View more details>"
                        }
                    ]
                }
            ],
        }
        attachments.append(attachment)
    logging.info(f"Slack attachments: {attachments}")
    return attachments


def post_message(channel: str, attachments: List):
    client = WebClient(token=os.environ.get('SLACK_TOKEN'))

    if len(attachments) == 0:
        return

    try:
        result = client.chat_postMessage(channel=channel, text="Failed check runs", attachments=attachments)
        logging.info(f"Message sent: {result}")
    except SlackApiError as e:
        if e.response.status_code == 429:
            delay = int(e.response.headers["Retry-After"])
            logging.info(f"Rate limited. Retrying in {delay} seconds.")
            time.sleep(delay)
            result = client.chat_postMessage(channel=channel, text="Failed check runs", attachments=attachments)
            logging.info(f"Message sent: {result}")
        else:
            logging.error(f"Error posting message: {e.response}")
            sys.exit(1)


def main():
    check_suite_id = os.environ.get('GITHUB_CHECK_SUITE_ID')
    repository = os.environ.get('GITHUB_REPOSITORY')
    github_actor_id = os.environ.get('GITHUB_ACTOR_ID')
    slack_channel = os.environ.get('SLACK_CHANNEL')

    logging.info(f"Retrieving failed check runs for {repository} and check suite ID: {check_suite_id}")
    try:
        repo = get_repo(repository)
        github_user = get_github_user_by_id(github_actor_id)
        slack_user = get_slack_user_by_name(github_user)
        check_suite = repo.get_check_suite(int(check_suite_id))
        failed_check_runs = get_failed_check_runs(check_suite)
        attachments = create_slack_attachments(failed_check_runs, repo.full_name, slack_user["id"] if slack_user else "")
        post_message(slack_channel, attachments)
        sys.exit(0)
    except GithubException as e:
        logging.error(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()
