import os
import csv
from github import Github
from github import Auth

def get_github_token():
    github_token = os.getenv('GITHUB_TOKEN')
    if not github_token:
        raise ValueError("GITHUB_TOKEN environment variable not set")
    return github_token

def mark_pr_as_ready(g, repo, pr_number):
    """Marks a pull request as ready for review (removes draft status)."""
    try:
        pr = repo.get_pull(pr_number)
        
        # Use the GraphQL API directly to mark the PR as ready for review
        # Get the node ID of the pull request
        node_id = pr.node_id
        
        # Construct and execute the GraphQL mutation
        query = """
        mutation MarkPullRequestReadyForReview {
          markPullRequestReadyForReview(input: {pullRequestId: "%s"}) {
            pullRequest {
              isDraft
            }
          }
        }
        """ % node_id
        
        # Execute the GraphQL query using the Github instance directly
        g._Github__requester.requestJsonAndCheck(
            "POST",
            "https://api.github.com/graphql",
            input={"query": query}
        )
        
        print(f"Pull request {pr_number} in {repo.full_name} marked as ready for review.")
    except Exception as e:
        print(f"Error marking pull request {pr_number} in {repo.full_name} as ready: {e}")

def main():
    github_token = get_github_token()
    auth = Auth.Token(github_token)
    g = Github(auth=auth)

    with open('pr_report.csv', 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            repository_name = row['repository']
            pr_url = row['pr_url']

            try:
                # Extract repository owner and name from the URL
                owner, repo_name = repository_name.split('/')

                # Extract pull request number from the URL
                pr_number = int(pr_url.split('/')[-1])

                repo = g.get_repo(f"{owner}/{repo_name}")
                mark_pr_as_ready(g, repo, pr_number)  # Pass g as the first parameter

            except Exception as e:
                print(f"Error processing {repository_name} - {pr_url}: {e}")

if __name__ == "__main__":
    main()