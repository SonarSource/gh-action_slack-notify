import os
import csv
from github import Github
from github import Auth

def get_github_token():
    github_token = os.getenv('GITHUB_TOKEN')
    if not github_token:
        raise ValueError("GITHUB_TOKEN environment variable not set")
    return github_token

def create_or_update_workflow(repo, workflow_file_path, slack_channel, action_ref, branch_name="migration-branch"):
    """
    Creates or updates a workflow file in the given repository within a new branch and creates a PR.
    """
    workflow_content = f"""---
name: Slack Notifications
on:
  check_suite:
    types: [completed]

jobs:
  notify:
    runs-on: ubuntu-latest
    steps:
      - name: Send Slack Notification
        uses: {action_ref}
        with:
          slackChannel: {slack_channel}
          slack_webhook_secret: ${{ secrets.SLACK_WEBHOOK }}
"""
    try:
        # Get the default branch
        default_branch = repo.default_branch
        main_branch = repo.get_branch(branch=default_branch)
        main_sha = main_branch.commit.sha

        # Create a new branch
        try:
            ref = repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=main_sha)
        except Exception as e:
            print(f"Branch {branch_name} already exists.  Continuing...")
            pass

        # Check if the file already exists
        try:
            contents = repo.get_contents(workflow_file_path, ref=branch_name)
            sha = contents.sha
            # Update the file
            repo.update_file(
                path=workflow_file_path,
                message=f"Update workflow with new Slack notification action",
                content=workflow_content,
                sha=sha,
                branch=branch_name
            )
            print(f"Updated workflow file: {workflow_file_path} in {repo.full_name} on branch {branch_name}")

        except Exception as e:
            # If the file doesn't exist, create it
            if e.status == 404:
                repo.create_file(
                    path=workflow_file_path,
                    message=f"Create workflow with new Slack notification action",
                    content=workflow_content,
                    branch=branch_name
                )
                print(f"Created workflow file: {workflow_file_path} in {repo.full_name} on branch {branch_name}")
            else:
                print(f"Error creating/updating workflow file: {workflow_file_path} in {repo.full_name}: {e}")
                return # Exit if there's an error

        # Create a pull request
        try:
            repo.create_pull(
                title=f"Update Slack notification in {workflow_file_path}",
                body=f"This PR updates the Slack notification action in {workflow_file_path}.",
                head=branch_name,
                base=default_branch
            )
            print(f"Created pull request for {repo.full_name}")
        except Exception as e:
            print(f"Error creating pull request for {repo.full_name}: {e}")


    except Exception as e:
        print(f"Error processing repository {repo.full_name}: {e}")


def main():
    github_token = get_github_token()
    auth = Auth.Token(github_token)
    g = Github(auth=auth)
    action_ref = 'SonarSource/gh-action_slack-notify@v1'  # Replace with your action's ref

    with open('migration_report_sample.csv', 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            repository_name = row['repository']
            workflow_file_name = row['workflow']
            slack_channel = row['slack_channel']

            repo = g.get_repo(repository_name)
            workflow_file_path = f".github/workflows/{workflow_file_name}"

            create_or_update_workflow(repo, workflow_file_path, slack_channel, action_ref)

if __name__ == "__main__":
    main()