import os
from typing import List

from github import Auth
from github import Github
from github import Repository
from github.CheckSuite import CheckSuite


def get_repo(repository: str) -> Repository:
    github_token = os.environ.get('GITHUB_TOKEN')
    auth = Auth.Token(github_token)
    g = Github(auth=auth)
    return g.get_repo(repository)


def get_failed_check_runs(check_suite: CheckSuite) -> List[CheckSuite]:
    check_runs = check_suite.get_check_runs()
    return [check_run for check_run in check_runs if check_run.conclusion == "failure"]


def main():
    github_env = os.environ.get('GITHUB_ENV')
    event_name = os.environ.get('GITHUB_EVENT')
    check_suite_id = os.environ.get('GITHUB_CHECK_SUITE_ID')
    repository = os.environ.get('GITHUB_REPOSITORY')

    if event_name == "check_run":
        with open(github_env, 'a') as env:
            env.write("event_type=check_run\n")
    else:
        print(f"Retrieving failed check runs for check suite ID: {
              check_suite_id}")
        repo = get_repo(repository)
        check_suite = repo.get_check_suite(int(check_suite_id))
        failed_check_runs = get_failed_check_runs(check_suite)
        for check_run in failed_check_runs:
            with open(github_env, 'a') as env:
                env.write(f"app_name={check_run.app.name}\n")
                env.write(f"conclusion={check_run.conclusion}\n")
                env.write(f"head_sha={check_run.head_sha}\n")


if __name__ == '__main__':
    main()
