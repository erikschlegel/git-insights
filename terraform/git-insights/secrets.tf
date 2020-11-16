data "azurerm_client_config" "current" {}

# https://www.terraform.io/docs/providers/azurerm/r/key_vault.html
resource "azurerm_key_vault" "kv" {
  name                = format("%s-kv", local.prefix)
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  tenant_id           = data.azurerm_client_config.current.tenant_id
  sku_name            = "standard"
}

# https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/key_vault_access_policy
resource "azurerm_key_vault_access_policy" "sp-manage" {
  key_vault_id            = azurerm_key_vault.kv.id
  tenant_id               = data.azurerm_client_config.current.tenant_id
  object_id               = data.azurerm_client_config.current.object_id
  key_permissions         = ["create", "delete", "get", "list", "update"]
  secret_permissions      = ["set", "delete", "get", "list"]
  certificate_permissions = ["create", "delete", "get", "list"]
}

resource "azurerm_key_vault_access_policy" "function-get" {
  key_vault_id       = azurerm_key_vault.kv.id
  tenant_id          = data.azurerm_client_config.current.tenant_id
  object_id          = azurerm_function_app.func.identity.0.principal_id
  secret_permissions = ["get"]
}

resource "azurerm_key_vault_secret" "token" {
  name         = "token"
  value        = var.token
  key_vault_id = azurerm_key_vault.kv.id
}