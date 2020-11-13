import logging

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import KeyVaultSecret
from azure.keyvault.secrets import SecretClient


class KeyvaultClient:
    def __init__(self, kvURI: str):
        self.kvURI: str = kvURI
        self.client: SecretClient = None

    def getSecretValue(self, secretName: str) -> KeyVaultSecret:
        self.setClientIfNotExists()

        try:
            return self.client.get_secret(secretName)
        except Exception:
            logging.error('Failed retrieving secret value for %s', secretName)
            raise

    def setClientIfNotExists(self) -> None:
        if self.client is None:
            credential = DefaultAzureCredential()
            try:
                self.client = SecretClient(vault_url=self.kvURI, credential=credential)
            except ValueError:
                logging.error("Required Key Vault information Error")
                raise
