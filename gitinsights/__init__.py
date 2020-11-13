import datetime
import json
import logging
import os

import azure.functions as func

from .mods.ado_client import AzureDevopsInsights
from .mods.kv_client import KeyvaultClient


def main(mytimer: func.TimerRequest, outputBlob: func.Out[func.InputStream]) -> None:
    # Required settings
    keyVaultName = os.environ["KeyvaultName"]
    patSecretName = os.environ["PatSecretName"]
    adoProject = os.environ["AdoProjectName"]
    adoOrg = os.environ["AdoOrgName"]
    repos = os.environ["AdoRepos"]
    teamId = os.environ["BacklogTeamId"]

    # Optional settings
    # Accounts for local git profile setup discrepencies
    aliasDict = json.loads(os.environ.get("ProfileAliases", "{}").replace("\'", "\""))

    groupByColumns = ['contributor', 'week', 'repo']

    if not keyVaultName or not patSecretName or not adoProject or not adoOrg or not repos:
        raise ValueError('Required environment variables are undefined')

    kvURI = f"https://{keyVaultName}.vault.azure.net"
    patToken = KeyvaultClient(kvURI).getSecretValue(patSecretName)

    utc_timestamp = datetime.datetime.utcnow().replace(
        tzinfo=datetime.timezone.utc).isoformat()

    if mytimer.past_due:
        logging.info('The timer is past due!')

    client = AzureDevopsInsights(adoOrg, adoProject, repos.split(','), teamId, aliasDict)
    dataframe = client.aggregatePullRequestActivity(groupByColumns, patToken.value)
    outputBlob.set(dataframe.to_csv(index=True))

    logging.info('Python timer trigger function ran at %s', utc_timestamp)
