# Terraform main.tf for Azure Container Apps pipeline

provider "azurerm" {
  features {}
}

resource "azurerm_resource_group" "main" {
  name     = var.resource_group
  location = var.location
}

resource "azurerm_storage_account" "main" {
  name                     = var.storage_account_name
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

resource "azurerm_storage_container" "audio" {
  name                  = "audio"
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "private"
}

resource "azurerm_storage_container" "chunks" {
  name                  = "chunks"
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "private"
}

resource "azurerm_storage_container" "transcripts" {
  name                  = "transcripts"
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "private"
}

resource "azurerm_container_registry" "main" {
  name                = var.acr_name
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "Basic"
  admin_enabled       = true
}

# Example for one ACA, repeat for each app
resource "azurerm_container_app" "download_and_prepare" {
  name                         = "download-and-prepare"
  resource_group_name          = azurerm_resource_group.main.name
  container_app_environment_id = var.aca_env_id
  revision_mode                = "Single"
  template {
    container {
      name   = "download-and-prepare"
      image  = "${azurerm_container_registry.main.login_server}/download-and-prepare:latest"
      env {
        name  = "BLOB_CONTAINER"
        value = azurerm_storage_container.audio.name
      }
      # ...other env vars...
    }
  }
}
