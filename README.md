# Slack Notification Action

This repository contains a reusable GitHub Action for sending build failure notifications to a Slack channel using a webhook.
This action should be called in a github workflow triggered by a check-run [completed] event.

## Inputs

The action accepts the following inputs:
- `slack_channel`: The Slack channel to which the notification will be sent. This input is required.
- `slack_webhook_secret`: The secret for the Slack webhook API. This input is required.
- `environment` : Name of the GitHub Environment to use. Required if your repository uses GitHub Environments with a modified OIDC sub claim. Set to `slack` in this case. default is to not use environments.

## Outputs

The action provides the following output:

- `notification_status`: The status of the Slack notification, indicating whether it was sent successfully or if there was an error.

## Supported platforms

Notifications will be triggered upon build failures in any of the following platforms

- SonarCloud
- SonarQube-Next
- CirrusCI
- Azure Pipelines

## Enabled branches

Slack notifications will be enabled only for builds in the following branches

- master
- main
- dogfood-\*
- branch-\*

## Requirements

The repository needs to be onboarded to [Vault](https://xtranet-sonarsource.atlassian.net/wiki/spaces/RE/pages/2466316312/HashiCorp+Vault#Onboarding-a-Repository-on-Vault).

## Usage

To use this action in your GitHub workflow, you can include it as follows:

```yaml
jobs:
  notify:
    runs-on: ubuntu-latest
    steps:
      - name: Send Slack Notification
        uses: SonarSource/gh-action_slack-notify@v1
        with:
          slack_channel: '#your-channel'
          slack_webhook_secret: ${{ SLACK_WEBHOOK }}
```

## Example

Here is an example of how to trigger the action on check suite completion:

```yaml
name: Notify Slack on Check Suite

on:
  check_suite:
    types: [completed]

jobs:
  notify:
    runs-on: ubuntu-latest
    steps:
      - name: Send Slack Notification
        uses: SonarSource/gh-action_slack-notify@v1
        with:
          ci_engine: 'cirrus-ci'
          slack_channel: '#your-channel'          
          slack_webhook_secret: ${{ secrets.SLACK_WEBHOOK }}
```

Here is an example of how to trigger the action manually using `workflow_dispatch`:

```yaml
name: Notify Slack

on:
  workflow_dispatch:
    inputs:
      slack_channel:
        description: 'Slack channel to send notification to'
        required: true
      slack_webhook_secret:
        description: 'Secret for Slack webhook API'
        required: true

jobs:
  notify:
    uses: SonarSource/gh-action_slack-notify/.github/workflows/main.yml
```

## Versioning

This project is using [Semantic Versioning](https://semver.org/).

Branches prefixed with a `v` are pointers to the last major versions, ie: [`v1`](https://github.com/SonarSource/gh-action_build-notify/tree/v1).

> Note: the `master` branch is used for development and can not be referenced directly. Use a `v` branch or a tag instead.

## Releases

To create a new release,

1. Draft a new release from Github releases page with the next semantic version.
2. Run `scripts/updatevbranch.sh <tag>` with the release version tag to update the v\* branch with the new tag.
