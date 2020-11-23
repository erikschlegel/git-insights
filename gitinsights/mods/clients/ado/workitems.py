from typing import Dict
from typing import List

import numpy as np
from dateutil import parser
from requests import Response

from ...managers.repo_insights_base import ApiClient
from ...managers.repo_insights_base import RepoInsightsManager


class AdoGetProjectWorkItemsClient(ApiClient):
    def getDeserializedDataset(self, **kwargs) -> List[dict]:
        required_args = {'teamId', 'project', 'repo'}
        RepoInsightsManager.checkRequiredKwargs(required_args, **kwargs)

        wiQLQuery = "Select [System.Id] From WorkItems Where [System.WorkItemType] = 'User Story' AND [State] <> 'Removed'"
        uri_parameters: Dict[str, str] = {}
        uri_parameters['api-version'] = "6.0"
        project: str = kwargs['project']
        teamId: str = kwargs['teamId']
        repo: str = kwargs['repo']

        resourcePath = "{}/{}/{}/_apis/wit/wiql".format(self.organization, project, teamId)
        return self.DeserializeResponse(self.PostResponse(resourcePath, {"query": wiQLQuery}, uri_parameters), project, repo)

    def GetResponse(self, resourcePath: str, uri_parameters: Dict[str, str]) -> Response:
        return self.sendGetRequest(resourcePath, uri_parameters)

    def PostResponse(self, resourcePath: str, json: dict, uri_parameters: Dict[str, str]) -> Response:
        return self.sendPostRequest(resourcePath, json, uri_parameters)

    def DeserializeResponse(self, response: Response, project: str, repo: str) -> List[dict]:
        recordList: List[dict] = []
        jsonResults = response.json()['workItems']

        recordsProcessed = 0
        topElements = 200

        while recordsProcessed < len(jsonResults):
            workitemIds = [str(w['id']) for w in jsonResults[recordsProcessed:topElements+recordsProcessed]]
            recordList += self.GetWorkitemDetails(workitemIds, project)
            recordsProcessed += topElements

        return self.ParseWorkitems(repo, recordList)

    def GetWorkitemDetails(self, workItemIds: List[str], project: str) -> List[dict]:
        if len(workItemIds) > 200:
            raise SystemError('The workitems API only supports up to 200 items for a single call.')

        uri_parameters: Dict[str, str] = {}
        uri_parameters['ids'] = ','.join(workItemIds)
        uri_parameters['api-version'] = "6.0"

        resourcePath = "{}/{}/_apis/wit/workitems".format(self.organization, project)

        return self.GetResponse(resourcePath, uri_parameters).json()['value']

    def ParseWorkitems(self, repo: str, workitems: List[dict]) -> List[dict]:
        recordList = []

        for workitem in workitems:
            recordList.append(
                {**self.reportableFieldDefaults, **{
                    'contributor': workitem['fields']['System.CreatedBy']['displayName'],
                    'week': parser.parse(workitem['fields']['System.CreatedDate']).strftime("%V"),
                    'repo': repo,
                    'user_stories_created': 1
                }})

            if {'Microsoft.VSTS.Common.ActivatedDate', 'System.AssignedTo'} <= set(workitem['fields']) and workitem['fields']['System.State'] != 'New':
                recordList.append(
                    {**self.reportableFieldDefaults, **{
                        'contributor': workitem['fields']['System.AssignedTo']['displayName'],
                        'week': parser.parse(workitem['fields']['Microsoft.VSTS.Common.ActivatedDate']).strftime("%V"),
                        'repo': repo,
                        'user_stories_assigned': 1,
                        'user_stories_completed': 1 if workitem['fields']['System.State'] in ['Closed', 'Resolved'] else 0,
                        'user_story_points_completed': workitem['fields']['Microsoft.VSTS.Scheduling.StoryPoints'] if workitem['fields']['System.State'] in ['Closed', 'Resolved'] and 'Microsoft.VSTS.Scheduling.StoryPoints' in workitem['fields'] else 0,
                        'user_story_points_assigned': workitem['fields']['Microsoft.VSTS.Scheduling.StoryPoints'] if 'Microsoft.VSTS.Scheduling.StoryPoints' in workitem['fields'] else 0,
                        'user_story_completion_days': RepoInsightsManager.dateStrDiffInDays(workitem['fields']['Microsoft.VSTS.Common.ResolvedDate'], workitem['fields']['Microsoft.VSTS.Common.ActivatedDate']) if workitem['fields']['System.State'] in ['Closed', 'Resolved'] else np.nan
                    }})

        return recordList
