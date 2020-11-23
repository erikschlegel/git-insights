from typing import Dict
from typing import List

from dateutil import parser
from requests import Response

from ...managers.repo_insights_base import ApiClient
from ...managers.repo_insights_base import RepoInsightsManager


class AdoPullRequestReviewCommentsClient(ApiClient):
    def getDeserializedDataset(self, **kwargs) -> List[dict]:
        required_args = {'repo', 'pullRequestId', 'project'}
        RepoInsightsManager.checkRequiredKwargs(required_args, **kwargs)

        pullrequestId = kwargs['pullRequestId']
        repo: str = kwargs['repo']
        project: str = kwargs['project']
        uri_parameters: Dict[str, str] = {}

        resourcePath = "{}/{}/_apis/git/repositories/{}/pullrequests/{}/threads".format(self.organization, project, repo, pullrequestId)
        return self.DeserializeResponse(self.GetResponse(resourcePath, uri_parameters), repo)

    def GetResponse(self, resourcePath: str, uri_parameters: Dict[str, str]) -> Response:
        return self.sendGetRequest(resourcePath, uri_parameters)

    def DeserializeResponse(self, response: Response, repo: str) -> List[dict]:
        recordList = []
        jsonResults = response.json()['value']

        for comments in jsonResults:
            recordList += self.DeserializeComments(comments['comments'], repo)

        return recordList

    def DeserializeComments(self, comments: List[dict], repo: str) -> List[dict]:
        recordList = []

        for comment in filter(lambda c: 'commentType' not in c or c['commentType'] != 'system', comments):
            recordList.append({**self.reportableFieldDefaults, **{
                'contributor': comment['author']['displayName'],
                'week': parser.parse(comment['lastUpdatedDate']).strftime("%V"),
                'pr_comments': 1,
                'repo': repo
            }
            })

        return recordList
