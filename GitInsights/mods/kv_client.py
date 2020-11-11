import logging

from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

class KeyvaultClient:
    def __init__(self, kvURI: str):
        self.kvURI: str = kvURI
        self.client: SecretClient = None

    def getSecretValue(self, secretName: str) -> str:
        self.setClientIfNotExists()

        try:
            return self.client.get_secret(secretName)
        except:
            logging.error("\nFailed retrieving secret value for {0}".format(secretName))
            raise

    def setClientIfNotExists(self) -> None:
        if self.client is None:
            credential = DefaultAzureCredential()
            try:
                self.client = SecretClient(vault_url=self.kvURI, credential=credential)
            except ValueError:
                logging.error("Required Key Vault information Error")
                raise