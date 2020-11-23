from enum import Enum
from typing import Dict
from typing import List

import numpy as np
from dateutil import parser
from requests import Response

from ...managers.repo_insights_base import ApiClient
from ...managers.repo_insights_base import RepoInsightsManager


class PullRequestVoteStatus(Enum):
    APPROVED = 10
    APPROVED_WITH_SUGGESTIONS = 5


class AdoPullRequestsClient(ApiClient):
    def getDeserializedDataset(self, **kwargs) -> List[dict]:
        required_args = {'repo', 'project'}
        RepoInsightsManager.checkRequiredKwargs(required_args, **kwargs)

        repo = kwargs['repo']
        project = kwargs['project']
        uri_parameters: Dict[str, str] = {}
        uri_parameters['searchCriteria.status'] = 'all'

        resourcePath = "{}/{}/_apis/git/repositories/{}/pullrequests".format(self.organization, project, repo)
        return self.DeserializeResponse(self.GetResponse(resourcePath, uri_parameters), repo)

    def GetResponse(self, resourcePath: str, uri_parameters: Dict[str, str]) -> Response:
        return self.sendGetRequest(resourcePath, uri_parameters)

    def DeserializePullRequest(self, pullrequest: dict, repo: str) -> dict:
        return {**self.reportableFieldDefaults,
                **{
                    'contributor': pullrequest['createdBy']['displayName'],
                    'prs_submitted': 1,
                    'prs_merged': 1 if pullrequest['status'] == 'completed' else 0,
                    'week': parser.parse(pullrequest['creationDate']).strftime("%V"),
                    'creation_datetime': parser.parse(pullrequest['creationDate']),
                    'completion_date': parser.parse(pullrequest['closedDate']) if pullrequest['status'] == 'completed' else np.nan,
                    'pr_completion_days': RepoInsightsManager.dateStrDiffInDays(pullrequest['closedDate'], pullrequest['creationDate']) if pullrequest['status'] == 'completed' else np.nan,
                    'repo': repo,
                    'pullRequestId': pullrequest['pullRequestId']
                },
                }

    def DeserializeResponse(self, response: Response, repo: str) -> List[dict]:
        recordList = []
        jsonResults = response.json()['value']

        for pr in jsonResults:
            recordList.append(self.DeserializePullRequest(pr, repo))

            for review in filter(lambda rv: rv['vote'] in [PullRequestVoteStatus.APPROVED.value, PullRequestVoteStatus.APPROVED_WITH_SUGGESTIONS.value] and 'isContainer' not in rv, pr['reviewers']):
                recordList.append(
                    {**self.reportableFieldDefaults, **{
                        'contributor': review['displayName'],
                        'week': parser.parse(pr['creationDate']).strftime("%V"),
                        'prs_reviewed': 1,
                        'repo': repo
                    }})

        return recordList
