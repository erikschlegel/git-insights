# Infrastructure as Code deployment through Terraform


## Configure environment

Many of the steps here assume that your shell environment is configured with the appropriate environment variables. You can find the required variables inside the relevant directory. Environment variables can be set using a tool like [direnv](https://direnv.net/), or by running the following:

```bash
DOT_ENV=.env
export $(cat $DOT_ENV | grep -v '^\s*#' | xargs)
```

## Initial Deployment

### Setup Terraform Backend State

Terraform state should live in a remote container in order to be leveraged across a variety of machines (developer workstations, CI agents, etc...). The `bootstrap` module provisions and configures the state container:

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

> **Note**: instructions for setting `ARM_ACCESS_KEY`, `ARM_ACCOUNT_NAME`, `ARM_CONTAINER_NAME` are described above.

```bash
cd git-insights
terraform init \
    -backend-config "storage_account_name=${ARM_ACCOUNT_NAME}" \
    -backend-config "container_name=${ARM_CONTAINER_NAME}"
terraform plan
terraform apply

# capture function name for deployment
FUNCTION_NAME=$(terraform output function-name)

cd ..
```

### Build & Deploy Azure Function

Now you should be able to deploy the function usign the command below:

> **Note**: this command should be run from the project root. Instructions for setting `FUNCTION_NAME` are described above.

```bash
func azure functionapp publish "$FUNCTION_NAME" --python
```
