# https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/app_service_plan
resource "azurerm_app_service_plan" "function-asp" {
  name                = format("%s-function-asp", local.prefix)
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  kind                = "FunctionApp"
  reserved            = true

  sku {
    tier = "Dynamic"
    size = "Y1"
  }
}

# https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/function_app
resource "azurerm_function_app" "func" {
  name                       = format("%s-function", local.prefix)
  location                   = azurerm_resource_group.rg.location
  resource_group_name        = azurerm_resource_group.rg.name
  app_service_plan_id        = azurerm_app_service_plan.function-asp.id
  storage_account_name       = azurerm_storage_account.sa.name
  storage_account_access_key = azurerm_storage_account.sa.primary_access_key
  os_type                    = "linux"
  version                    = "~3"

  identity {
    type = "SystemAssigned"
  }

  site_config {
    linux_fx_version = "PYTHON|3.8"
  }

  app_settings = {
    FUNCTIONS_WORKER_RUNTIME : "python"
    APPINSIGHTS_INSTRUMENTATIONKEY : azurerm_application_insights.ai.instrumentation_key

    AzureWebJobsStorage : azurerm_storage_account.sa.primary_connection_string
    gitinsights_STORAGE : azurerm_storage_account.sa.primary_connection_string

    KeyvaultName : azurerm_key_vault.kv.name
    PatSecretName : azurerm_key_vault_secret.token.name

    AdoRepos : join(",", var.ado_config.repo_names)
    AdoOrgName : var.ado_config.org_name
    BacklogTeamId : var.ado_config.backlog_team_name
    AdoProjectName : var.ado_config.project_name
    ProfileAliases : jsonencode(var.ado_config.profile_aliases)
  }
}
