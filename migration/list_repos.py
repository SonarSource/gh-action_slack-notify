import os
from github import Github
import csv
import base64
import time  # Import the time module

def get_github_token():
    github_token = os.getenv('GITHUB_TOKEN')
    if not github_token:
        raise ValueError("GITHUB_TOKEN environment variable not set")
    return github_token

def get_first_non_comment_line(content):
    lines = content.split('\n')
    for line in lines:
        if not line.strip().startswith('#'):
            return line.strip()
    return None

def find_action_in_workflow(workflow_content, action_name):
    return action_name in workflow_content

def main():
    github_token = get_github_token()
    print(f"Getting github token from environment variable: GITHUB_TOKEN")
    g = Github(github_token)
    org_name = 'SonarSource'
    action_name = 'SonarSource/gh-action_build-notify'

    results = []

    org = g.get_organization(org_name)
    for repo in org.get_repos():
        if repo.archived:
            continue

        workflows_path = ".github/workflows"
        try:
            try:
                repo.get_contents(workflows_path)
            except Exception as e:
                #print(f"Repository {repo.full_name} does not have a .github/workflows directory: {e}")
                continue

            try:
                contents = repo.get_contents(workflows_path)
                if not isinstance(contents, list):
                    continue
            except Exception as e:
                print(f"Error getting contents for {repo.full_name}: {e}")
                continue

            for workflow_file in contents:
                try:
                    # Check if the item is a file before attempting to decode
                    if workflow_file.type == 'file':
                        workflow_content = workflow_file.decoded_content.decode('utf-8')
                        if find_action_in_workflow(workflow_content, action_name):
                            try:
                                codeowners_file = repo.get_contents(".github/CODEOWNERS")
                                codeowners_content = codeowners_file.decoded_content.decode('utf-8')
                                first_non_comment_line = get_first_non_comment_line(codeowners_content)
                            except Exception as e:
                                first_non_comment_line = None

                            result = {
                                'repository': repo.full_name,
                                'workflow': workflow_file.name,
                                'codeowners': first_non_comment_line
                            }
                            results.append(result)
                            print(f"Repository: {repo.full_name}, Workflow: {workflow_file.name}, CODEOWNERS: {first_non_comment_line}")
                    else:
                        print(f"Skipping non-file item: {workflow_file.name} in {repo.full_name}")
                except Exception as e:
                    print(f"Error processing workflow {workflow_file.name} in {repo.full_name}: {e}")
                time.sleep(1) # Add a delay to avoid rate limiting

        except Exception as e:
            print(f"Error processing repository {repo.full_name}: {e}")

    # Write results to CSV file
    with open('migration_report.csv', 'w', newline='') as csvfile:
        fieldnames = ['repository', 'workflow', 'codeowners']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for row in results:
            writer.writerow(row)

if __name__ == "__main__":
    main()