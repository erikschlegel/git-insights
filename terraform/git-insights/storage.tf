# https://www.terraform.io/docs/providers/azurerm/r/storage_account.html
resource "azurerm_storage_account" "sa" {
  name                     = substr(replace(format("%s-storage", local.prefix), "-", ""), 0, 24)
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_replication_type = "GRS"
  account_tier             = "Standard"
  allow_blob_public_access = false
  tags                     = local.tags
}
