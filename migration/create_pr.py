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
    Returns the URL of the created PR, or None if an error occurred.
    """
    workflow_content = f"""---
name: Slack Notifications
on:
  check_suite:
    types: [completed]

permissions:
  contents: read
  checks: read
  id-token: write

jobs:
  slack-notifications:
    if: >-
      contains(fromJSON('["main", "master"]'), github.event.check_suite.head_branch) || startsWith(github.event.check_suite.head_branch, 'dogfood-') || startsWith(github.event.check_suite.head_branch, 'branch-')
    runs-on: sonar-runner
    steps:
      - name: Send Slack Notification
        env:
          GITHUB_TOKEN: ${{ github.token }}
        uses: SonarSource/gh-action_slack-notify@1.0.0
        with:
          slackChannel: {slack_channel}
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
                return None # Exit if there's an error

        # Create a pull request
        try:
            pr = repo.create_pull(
                title=f"Update Slack notification in {workflow_file_path}",
                body=f"This PR updates the Slack notification action in {workflow_file_path}.",
                head=branch_name,
                base=default_branch,
                draft=True  # Create the PR in draft mode
            )
            print(f"Created pull request for {repo.full_name}")
            return pr.html_url  # Return the URL of the created PR
        except Exception as e:
            print(f"Error creating pull request for {repo.full_name}: {e}")
            return None # Return None if there's an error

    except Exception as e:
        print(f"Error processing repository {repo.full_name}: {e}")
        return None # Return None if there's an error


def main():
    github_token = get_github_token()
    auth = Auth.Token(github_token)
    g = Github(auth=auth)
    action_ref = 'SonarSource/gh-action_slack-notify@v1'  # Replace with your action's ref

    pr_urls = []  # List to store PR URLs

    with open('migration_report.csv', 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            repository_name = row['repository']
            workflow_file_name = row['workflow']
            slack_channel = row['slack_channel']

            repo = g.get_repo(repository_name)
            workflow_file_path = f".github/workflows/{workflow_file_name}"

            pr_url = create_or_update_workflow(repo, workflow_file_path, slack_channel, action_ref)
            if pr_url:
                pr_urls.append({'repository': repository_name, 'workflow': workflow_file_name, 'pr_url': pr_url})

    # Write PR URLs to CSV file
    with open('pr_report.csv', 'w', newline='') as csvfile:
        fieldnames = ['repository', 'workflow', 'pr_url']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(pr_urls)

if __name__ == "__main__":
    main()