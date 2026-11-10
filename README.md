# Slack Notification Action

> **⚠️ Legacy Action Notice**
>
> This action is **only compatible with legacy Cirrus CI notifications** based on GitHub check suite events.
>
> **For modern GitHub Actions workflows**, please use
> [step-security/slack-github-action](https://github.com/step-security/slack-github-action)
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

For modern GitHub Actions workflows, use
[step-security/slack-github-action](https://github.com/step-security/slack-github-action) v4.0.0
(`fd40160713f6a8cec8aceb5c1e3c0a1e42960eb2`) with SonarSource Vault integration.
It is the StepSecurity-maintained fork of Slack's official action. Pin that commit.
It runs on our hosted runners: `sonar-xs` for private repositories and `sonar-xs-public` for public ones.

```yaml
---
jobs:
  notify:
    runs-on: sonar-xs # public repositories use sonar-xs-public
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

      - name: Slack Notification
        uses: step-security/slack-github-action@fd40160713f6a8cec8aceb5c1e3c0a1e42960eb2 # v4.0.0
        with:
          method: chat.postMessage
          token: ${{ fromJSON(steps.secrets.outputs.vault).SLACK_TOKEN }}
          payload: |
            channel: your-channel-name
            text: |
              Workflow failed in ${{ github.repository }}
              ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}
              Branch: ${{ github.ref_name }}
```

### Channel Configuration

- **Public channels**: Messages can be sent by default
- **Private channels**: The `build_notifier` application integration must be added to the channel before notifications can be received

## Releases

To create a new release:

1. Draft a new release from GitHub releases page with the next semantic version.
