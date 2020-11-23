from typing import Dict
from typing import List

from requests import Response

from ...managers.repo_insights_base import ApiClient


# We need to fetch the org profiles to account for local git profile <> ADO profile discrepencies
class AdoGetOrgEntitlementsClient(ApiClient):
    # pylint: disable=unused-argument
    def getDeserializedDataset(self, **kwargs) -> List[dict]:
        uri_parameters: Dict[str, str] = {}

        resourcePath = "{}/_apis/graph/users".format(self.organization)
        return [AdoGetOrgEntitlementsClient.DeserializeResponse(self.GetResponse(resourcePath, uri_parameters))]

    def GetResponse(self, resourcePath: str, uri_parameters: Dict[str, str]) -> Response:
        return self.sendGetRequest(resourcePath, uri_parameters)

    @staticmethod
    def DeserializeResponse(response: Response) -> Dict[str, str]:
        jsonResults = response.json()['value']

        return {
            profile['principalName'].lower(): profile['displayName'] for profile in jsonResults if profile['origin'] == 'aad'
        }
