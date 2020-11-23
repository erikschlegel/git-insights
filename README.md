# Git-based SCM Insights SDK
- [Git-based SCM Insights SDK](#git-based-scm-insights-sdk)
  - [Overview](#overview)
    - [Supported Source Code Management Providers](#supported-source-code-management-providers)
    - [ADO Insight Capabilities](#ado-insight-capabilities)
    - [Reportable Fields](#reportable-fields)
  - [Installation](#installation)
    - [Option 1 - Install with pip](#option-1---install-with-pip)
    - [Option 2 - Deploy to Azure with Terraform](#option-2---deploy-to-azure-with-terraform)
    - [Option 3 - Setup local Azure Function environment](#option-3---setup-local-azure-function-environment)
      - [Azure Function Prerequisites](#azure-function-prerequisites)
      - [Steps](#steps)
  - [SDK Usage](#sdk-usage)
    - [Example](#example)
  - [Backlog Features - will be migrated to repo backlog](#backlog-features---will-be-migrated-to-repo-backlog)
  - [Contributing](#contributing)

[![Build Status](https://travis-ci.com/erikschlegel/git-insights.svg?branch=main)](https://travis-ci.com/erikschlegel/git-insights)
[![codecov](https://codecov.io/gh/erikschlegel/git-insights/branch/main/graph/badge.svg)](https://codecov.io/gh/erikschlegel/git-insights)
[![PyPI version](https://badge.fury.io/py/gitinsights.svg)](https://badge.fury.io/py/gitinsights)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/gitinsights.svg)](https://pypi.org/project/gitinsights/)
[![PyPI - License](https://img.shields.io/pypi/l/gitinsights.svg)](https://pypi.org/project/gitinsights/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/gitinsights.svg)](https://pypi.org/project/gitinsights/)


`git-insights` is a _work in progress / early days_ toolset enabling engineering leads to gain insights around how a team is collaborating towards a project's workitems and codebase. Devs can use this sdk to identify opportunities to collectively help other team members improve collaboration.

`git-insights` connects to your existing source code management repositories and work item activities to provide insights toward active and completed scheduled work, git commits, pull requests and code reviews. The dataset can also be used to collectively celebrate progress week over week.

## Overview

### Supported Source Code Management Providers
- [Azure Dev OPS](https://azure.microsoft.com/en-us/services/devops/)
- GitLab (_coming soon_)
- GitHub (_coming soon_)

### ADO Insight Capabilities
 - Active / completed workitems (_incl duration averages_)
 - Workitem creation
 - Pushed commits
 - Git commit log stats (_ie sum of line edits, additions, deletions_)
 - Active / completed story points
 - Active / completed pull requests (_incl duration averages_)
 - Code review comments + reviews
 - Azure Function integration to support report scheduling and delivery

### Reportable Fields

[Sample Dataset](data_samples/seinfeld_trivia.csv)

| Field Name  | Description | Type |
| ------------- | ------------- | ------------- |
| `contributor`  | The profile display name of the activity contributor / assignee  | `String` |
| `week`  | The week of year for the captured activity  | `int` |
| `repo`  | The git repository name  | `String` |
| `prs_merged`  | Sum of pull requests merged into the `main` branch  | `int` |
| `prs_submitted`  | Sum of pull requests submitted for review  | `int` |
| `pr_completion_days`  | Mean Average duration for pull request review (_ie days diff between PR submission date and completion date_)  | `float` |
| `pr_comments`  | Sum of posted pull request review comments | `int` |
| `prs_reviewed`  | Sum of submitted pull requests reviewed | `int` |
| `pr_commits_pushed`  | Sum of git commits pushed to active pull requests | `int` |
| `commit_change_count_edits`  | Sum of changed lines within the commit log | `int` |
| `commit_change_count_deletes`  | Sum of removed lines within the commit log | `int` |
| `commit_change_count_additions`  | Sum of newly added lines within the commit log | `int` |
| `user_stories_assigned`  | Sum of user stories assigned to the contributor | `int` |
| `user_stories_completed`  | Sum of user stories completed or resolved by the contributor | `int` |
| `user_story_points_assigned`  | Sum of story points asssigned to the contributor | `int` |
| `user_story_points_completed`  | Sum of completed story points | `int` |
| `user_story_completion_days`  | Mean Average duration for user story completion (_ie days diff between story assignment and completion date_) | `float` |
| `user_stories_created`  | Sum of user stories created | `int` |

## Installation

This SDK can be used either through the pip package or as an Azure Function.

**Prerequisites**
- An Azure Subscription
- An [ADO PAT Token](https://docs.microsoft.com/en-us/azure/devops/organizations/accounts/use-personal-access-tokens-to-authenticate?view=azure-devops&tabs=preview-page#create-a-pat) with read permissions scoped to Code, Work Items and Graph.
- An ADO organization, project, repo(s) and a backlog team
- All project dependencies such as Python, Azure Functions CLI and Terraform are configured as an easy to consume [Development Container](https://code.visualstudio.com/docs/remote/containers). To use this, install the [Remote Development Extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.vscode-remote-extensionpack) and then follow [these instructions](https://code.visualstudio.com/docs/remote/containers#_quick-start-open-an-existing-folder-in-a-container) for opening the workspace in the containerized environment.

### Option 1 - Install with pip

```
pip install gitinsights
```

### Option 2 - Deploy to Azure with Terraform

This application can be easily deployed to Azure using Terraform by following the [Terraform Getting Started Guide](./terraform/README.md)

### Option 3 - Setup local Azure Function environment

#### Azure Function Prerequisites
- VSCode
- [Azure Blob Storage Account](https://docs.microsoft.com/en-us/azure/storage/blobs/storage-blob-create-account-block-blob?tabs=azure-portal)
- [Keyvault Resource](https://docs.microsoft.com/en-us/azure/key-vault/secrets/quick-create-portal#create-a-vault)
- A [secret](https://docs.microsoft.com/en-us/azure/key-vault/secrets/quick-create-portal#add-a-secret-to-key-vault) containing the value of your PAT token.
- [Service Principal](https://docs.microsoft.com/en-us/azure/active-directory/develop/howto-create-service-principal-portal) with read level role assignments into the above Keyvault resource

#### Steps
1. Clone the repo
```
git clone https://github.com/erikschlegel/git-insights.git
cd git-insights
pip install -r requirements.txt && pip install -r requirements-dev.txt
```

2. Once the Azure extension is installed, sign into your Azure account by navigating to the Azure explorer, select Sign in to Azure under Functions, and follow the prompts in the browser.
![](https://docs.microsoft.com/en-us/azure/developer/python/media/tutorial-vs-code-serverless-python/azure-sign-in.png)

After signing in, verify that the status bar says Azure: Signed In and your subscription(s) appears in the Azure explorer:

![](https://docs.microsoft.com/en-us/azure/developer/python/media/tutorial-vs-code-serverless-python/azure-account-status-bar.png)

3. To verify that all the Azure Functions tools are installed, open the Visual Studio Code Command Palette (F1), select the Terminal: Create New Integrated Terminal command, and once the terminal opens, run the command `func`

![](https://docs.microsoft.com/en-us/azure/developer/python/media/tutorial-vs-code-serverless-python/check-azure-functions-tools-prerequisites-in-visual-studio-code.png)

4. Configuration Setup
- Rename `local.settings.json.template` -> `local.settings.json`
- Provide the Azure storage account's primary connection string for both the `gitinsights_STORAGE` and `AzureWebJobsStorage` settings.
- Provide the service principal credentials for the following settings: `AZURE_CLIENT_SECRET`, `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_SUBSCRIPTION_ID`
- Provide the keyvault name for the `KeyvaultName` setting, and the secret containing the PAT token for the `PatSecretName` setting
- Provide the ADO organization name, project name, repositories (comma delimited for multiple) and backlog [team name](https://docs.microsoft.com/en-us/azure/devops/organizations/settings/add-teams?bc=%2Fazure%2Fdevops%2Fboards%2Fbreadcrumb%2Ftoc.json&toc=%2Fazure%2Fdevops%2Fboards%2Ftoc.json&view=azure-devops&tabs=preview-page).

5. Set a breakpoint in the code and hit F5 to debug locally.

6. The function will write the results to your blob storage account prior to completion.

_JFYI_: This particular Azure Function is scheduled to run every friday at 9AM. Edit [`functions.json`](./gitinsights/function.json) if you'd like to change the [NCRONTAB schedule](https://docs.microsoft.com/en-us/azure/azure-functions/functions-bindings-timer?tabs=csharp#ncrontab-examples).

## SDK Usage

### Example

```python
from gitinsights.mods.managers.ado import AzureDevopsClientManager

adoProject = "Seinfeld-Trivia"
adoOrg = "Best-Shows"
repos = ["Tales-of-Kramer"]
teamId = "Team LD"
patToken = "Kramers-secret"

groupByColumns = ['contributor', 'week', 'repo']

client = AzureDevopsClientManager(adoOrg, adoProject, repos, teamId, patToken)
dataframe = client.aggregatePullRequestActivity(groupByColumns)

print(dataframe)
```

## Backlog Features - will be migrated to repo backlog
- Azure Functions Integration
  - Dockerize Azure Function
  - Add Azure Function Continuous Delivery Pipeline
  - Integrate with PowerBI
  - Terraform integration to automate scaffolding of keyvault, azure function and blob storage resources
- Add E2E Integration Tests
- Add pre-commit hook to block pushes including creds
- Add a new provider to support Git Lab integration
- Integrate [Sphinx](https://www.sphinx-doc.org/en/master/) to autogen SDK docs

## Contributing

============

You can contribute to the project in multiple ways:

* Write documentation
* Implement features
* Fix bugs
* Add unit and functional tests
* Everything else you can think of