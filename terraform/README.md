# Infrastructure as Code deployment through Terraform

This document walks you through deploying and configuring the `gitinsights` function through Terraform. Specifically, the templates here will deploy the following:

* Storage account and container used to hold [Terraform state](https://www.terraform.io/docs/state/remote.html). These are kept in a separate resource group from the service deployment.
* Resource group for `gitinsights` function deployment
* KeyVault for hosting Azure DevOps token. The token is automatically created as a secret in this vault
* Consumption App Service Plan
* Azure Function with Managed Identity that can consume secrets from KeyVault

## Configure environment

Many of the steps here assume that your shell environment is configured with the appropriate environment variables. You can find the required variables inside the relevant directory. Environment variables can be set using a tool like [direnv](https://direnv.net/), or by running the following:

```bash
DOT_ENV=.env
export $(cat $DOT_ENV | grep -v '^\s*#' | xargs)
```

## Initial Deployment

### Setup Terraform Backend State

Terraform state should live in a remote container in order to be leveraged across a variety of machines (developer workstations, CI agents, etc...). The `bootstrap` module provisions and configures the state container:

> **Note**: ensure that the [required environment variables](./bootstrap/.env.template) are properly configured

```bash
cd bootstrap/
terraform apply

# capture backend state configuration
ARM_ACCESS_KEY=$(terraform output backend-state-account-key)
ARM_ACCOUNT_NAME=$(terraform output backend-state-account-name)
ARM_CONTAINER_NAME=$(terraform output backend-state-container-name)

cd ..
```

### Deploy Infrastructure

Now that the remote state container is configured it is possible to deploy the infrastructure:

> **Note**: ensure that the [required environment variables](./git-insights/.env.template) are properly configuredInstructions for setting `ARM_ACCESS_KEY`, `ARM_ACCOUNT_NAME`, `ARM_CONTAINER_NAME` are described above.
>
> Also, provide the [required terraform variables](./git-insights/config.tfvars.template) with setting `profile_aliases(i.e. {"cosmo@kramerica.com": "Cosmo Kramer"})`, `project_name`, `org_name`, `repo_names`, `backlog_team_name`, `token`.

```bash
cd git-insights
terraform init \
    -backend-config "storage_account_name=${ARM_ACCOUNT_NAME}" \
    -backend-config "container_name=${ARM_CONTAINER_NAME}"
terraform plan -var-file="config.tfvars"
terraform apply -var-file="config.tfvars"

# capture function name for deployment
FUNCTION_NAME=$(terraform output function-name)

cd ..
```

### Build & Deploy Azure Function

Now you should be able to deploy the function using the command below:

> **Note**: this command should be run from the project root. Instructions for setting `FUNCTION_NAME` are described above.

```bash
func azure functionapp publish "$FUNCTION_NAME" --python
```
