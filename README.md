# gh-action_slack-notify

GitHub Action to send Slack notifications for failed GitHub Checks.

## Test the action locally

Install [act](https://nektosact.com/installation/index.html) then run:

```bash
act --pull=false -P sonar-runner=catthehacker/ubuntu:full-latest -j build -e event.json
```
