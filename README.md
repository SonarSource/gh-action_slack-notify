# Slack Notification Action

> **⚠️ Legacy Action Notice**
>
> This action is **only compatible with legacy Cirrus CI notifications** based on GitHub check suite events.
>
> **For modern GitHub Actions workflows**, please use [rtCamp/action-slack-notify](https://github.com/rtCamp/action-slack-notify)
> instead (see [Recommended Alternative](#recommended-alternative) below).

This repository provides a GitHub Action for sending build failure notifications to a Slack channel.
This action is designed to be called in a GitHub Workflow triggered by a check-suite [completed] event, specifically for CirrusCI integration.

## Inputs

The action accepts the following inputs:

- `slackChannel`: The Slack channel to which the notification will be sent. This input is required.

## Requirements

The repository needs to be onboarded to [Vault](https://xtranet-sonarsource.atlassian.net/wiki/spaces/RE/pages/2466316312/HashiCorp+Vault#Onboarding-a-Repository-on-Vault).

## Legacy Usage (Cirrus CI Only)

> **Note**: This section is only relevant for legacy Cirrus CI integrations. For new projects, use the recommended alternative above.

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

## Recommended Alternative

For modern GitHub Actions workflows, we recommend using
[rtCamp/action-slack-notify](https://github.com/rtCamp/action-slack-notify) with SonarSource Vault integration:

```yaml
---
jobs:
  notify:
    runs-on: github-ubuntu-latest-s # Public GitHub hosted runner required, Self-Hosted runners do not support Docker-in-Docker
    permissions:
      id-token: write
    if: failure()
    steps:
      - name: Vault Secrets
        id: secrets
        uses: SonarSource/vault-action-wrapper@v3
        with:
          secrets: |
            development/kv/data/slack token | SLACK_TOKEN;

      - name: Slack Notification rtCamp
        uses: rtCamp/action-slack-notify@e31e87e03dd19038e411e38ae27cbad084a90661 # v2.3.3
        env:
          SLACK_TOKEN: >-
            ${{ fromJSON(steps.secrets.outputs.vault).SLACK_TOKEN }}
          SLACK_CHANNEL: your-channel-name
          SLACK_TITLE: Build Failed
          SLACK_MESSAGE: |
            Workflow failed in ${{ github.repository }} 🚨
            ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}
            Branch: ${{ github.event.workflow_run.head_branch }}

          SLACK_USERNAME: BuildBot
          SLACK_COLOR: danger
```

### Channel Configuration

- **Public channels**: Messages can be sent by default
- **Private channels**: The `build_notifier` application integration must be added to the channel before notifications can be received

## Releases

To create a new release:

1. Draft a new release from GitHub releases page with the next semantic version.
