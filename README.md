# Slack Notification Action

This repository aim to provide a GitHub Action for sending build failure notifications to a Slack channel.
This action should be called in a GitHub Workflow triggered by a check-suite [completed] event.

## Inputs

The action accepts the following inputs:

- `slackChannel`: The Slack channel to which the notification will be sent. This input is required.

## Requirements

The repository needs to be onboarded to [Vault](https://xtranet-sonarsource.atlassian.net/wiki/spaces/RE/pages/2466316312/HashiCorp+Vault#Onboarding-a-Repository-on-Vault).

## Usage

Here is an example of how to trigger the action on check suite completion for the protected branches only:

```yaml
---
name: Slack Notifications
on:
  check_suite:
    types: [completed]

permissions:
  contents: read
  id-token: write
  checks: read
jobs:
  notify:
    runs-on: ubuntu-latest
    steps:
      - name: Send Slack Notification
        if: |
          github.base_ref == 'main' ||
          github.base_ref == 'master' ||
          startsWith(github.base_ref, 'branch-') ||
          startsWith(github.base_ref, 'dogfood-')
        env:
          GITHUB_TOKEN: ${{ github.token }}
        uses: SonarSource/gh-action_slack-notify@1.0.0
        with:
          slackChannel: channel_name
```

## Releases

To create a new release:

1. Draft a new release from GitHub releases page with the next semantic version.
