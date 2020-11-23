import json
import os
from typing import List
from typing import Set
from unittest import TestCase
from unittest.mock import Mock
from unittest.mock import patch

from requests.models import Response

from gitinsights.mods.managers.ado import AdoGetOrgEntitlementsClient
from gitinsights.mods.managers.ado import AdoGetProjectWorkItemsClient
from gitinsights.mods.managers.ado import AdoPullRequestCommitsClient
from gitinsights.mods.managers.ado import AdoPullRequestReviewCommentsClient
from gitinsights.mods.managers.ado import AdoPullRequestsClient
from gitinsights.mods.managers.ado import AzureDevopsClientManager


def loadMockFile(filePath: str):
    with open(os.path.join(os.path.dirname(__file__), filePath)) as f:
        return json.load(f)


def aggregateColumn(dataset: List[dict], column: str) -> int:
    return sum(row[column] for row in dataset)


def JsonToResponse(dataset: dict, status: int = 400) -> Response:
    the_response = Mock(spec=Response)
    the_response.status_code = status
    the_response.json.return_value = dataset

    return the_response


# pylint: disable=too-many-instance-attributes
class Test_ADOPrStatService(TestCase):
    def setUp(self):
        self.mockedRepoPrResponse = loadMockFile("./data/prStatsByProject.json")
        self.mockedPrThreadsResponse = loadMockFile("./data/prThreads.json")
        self.mockedPrCommitsResponse = loadMockFile("./data/prCommits.json")
        self.mockedRepoCommitsResponse = loadMockFile("./data/repoCommits.json")
        self.mockedWorkitemListResponse = loadMockFile("./data/workitemList.json")
        self.mockedWorkitemDetailsResponse = loadMockFile("./data/workitemDetails.json")
        self.mockedEntitlementReponse = loadMockFile("./data/entitlements.json")
        self.clientManager = AzureDevopsClientManager("myorg", "my-super-project", ["repo1"], "team-buffalo", "token-1")

    def get_mocked_reponse_side_effects(self, clients: Set[str]) -> List[Response]:
        sideEffects: List[Response] = []

        if 'entitlements' in clients:
            sideEffects += [JsonToResponse(self.mockedEntitlementReponse)]

        if 'pullrequest' in clients:
            sideEffects += [JsonToResponse(self.mockedRepoPrResponse)]

        if 'commits' in clients:
            sideEffects += [JsonToResponse(self.mockedPrCommitsResponse), JsonToResponse(self.mockedRepoCommitsResponse)]

        if 'comments' in clients:
            sideEffects += [JsonToResponse(self.mockedPrThreadsResponse)]

        if 'workitems' in clients:
            sideEffects += [JsonToResponse(self.mockedWorkitemDetailsResponse)]

        return sideEffects

    @patch('gitinsights.mods.managers.repo_insights_base.requests.get')
    def test_repo_pr_list(self, mock_get):
        mock_get.return_value.json.return_value = self.mockedRepoPrResponse
        # pylint: disable=protected-access
        client = AdoPullRequestsClient("myorg", "dev.azure.com", "6.0", "", self.clientManager._reportableFieldDefaults)
        response = client.getDeserializedDataset(repo="repo1", project=self.clientManager.project)
        with self.assertRaises(ValueError):
            client.getDeserializedDataset(project=self.clientManager.project)

        self.assertEqual(len(response), 5)
        self.assertEqual(aggregateColumn(response, 'prs_reviewed'), 1)
        self.assertEqual(aggregateColumn(response, 'prs_merged'), 1)
        self.assertEqual(aggregateColumn(response, 'prs_submitted'), 4)

    @patch('gitinsights.mods.managers.repo_insights_base.requests.get')
    def test_repo_pr_comments(self, mock_get):
        mock_get.return_value.json.return_value = self.mockedPrThreadsResponse
        pullRequestId = "112"
        # pylint: disable=protected-access
        client = AdoPullRequestReviewCommentsClient("myorg", "dev.azure.com", "6.0", "", self.clientManager._reportableFieldDefaults)
        response = client.getDeserializedDataset(repo="repo1", project=self.clientManager.project, pullRequestId=pullRequestId)

        with self.assertRaises(ValueError):
            client.getDeserializedDataset(project=self.clientManager.project)

        self.assertEqual(len(response), 3)
        self.assertEqual(aggregateColumn(response, 'pr_comments'), 3)

    @patch('gitinsights.mods.managers.repo_insights_base.requests.get')
    def test_repo_pr_commits(self, mock_get):
        mock_get.side_effect = self.get_mocked_reponse_side_effects({'entitlements', 'commits'})
        # pylint: disable=protected-access
        client = AdoGetOrgEntitlementsClient("myorg", "dev.azure.com", "6.0", "", self.clientManager._reportableFieldDefaults)
        entitlements = client.getDeserializedDataset()[0]

        pullRequestId = "112"
        # pylint: disable=protected-access
        client = AdoPullRequestCommitsClient("myorg", "dev.azure.com", "6.0", "", self.clientManager._reportableFieldDefaults)
        response = client.getDeserializedDataset(repo="repo1", project=self.clientManager.project, pullRequestId=pullRequestId, entitlements=entitlements)

        with self.assertRaises(ValueError):
            client.getDeserializedDataset(project=self.clientManager.project)

        self.assertEqual(len(response), 8)
        self.assertEqual(aggregateColumn(response, 'pr_commits_pushed'), 8)
        self.assertEqual(aggregateColumn(response, 'commit_change_count_deletes'), 3)
        self.assertEqual(aggregateColumn(response, 'commit_change_count_additions'), 5)
        self.assertEqual(aggregateColumn(response, 'commit_change_count_edits'), 0)

    @patch('gitinsights.mods.managers.repo_insights_base.requests.get')
    @patch('gitinsights.mods.managers.repo_insights_base.requests.post')
    def test_project_workitems(self, mock_post, mock_get):
        mock_get.return_value.json.return_value = self.mockedWorkitemDetailsResponse
        mock_post.return_value.json.return_value = self.mockedWorkitemListResponse
        # pylint: disable=protected-access
        client = AdoGetProjectWorkItemsClient("myorg", "dev.azure.com", "6.0", "", self.clientManager._reportableFieldDefaults)
        response = client.getDeserializedDataset(repo="repo1", project=self.clientManager.project, teamId=self.clientManager.teamId)

        with self.assertRaises(ValueError):
            client.getDeserializedDataset(project=self.clientManager.project)

        self.assertEqual(len(response), 5)
        self.assertEqual(aggregateColumn(response, 'user_stories_created'), 3)
        self.assertEqual(aggregateColumn(response, 'user_stories_assigned'), 2)
        self.assertEqual(aggregateColumn(response, 'user_stories_completed'), 1)

    @patch('gitinsights.mods.clients.ado.entitlements.AdoGetOrgEntitlementsClient.GetResponse')
    @patch('gitinsights.mods.clients.ado.pull_request.AdoPullRequestsClient.GetResponse')
    @patch('gitinsights.mods.clients.ado.commits.AdoPullRequestCommitsClient.GetCommitsByRepoResponse')
    @patch('gitinsights.mods.clients.ado.commits.AdoPullRequestCommitsClient.GetCommitsByPrResponse')
    @patch('gitinsights.mods.clients.ado.comments.AdoPullRequestReviewCommentsClient.GetResponse')
    @patch('gitinsights.mods.clients.ado.workitems.AdoGetProjectWorkItemsClient.PostResponse')
    @patch('gitinsights.mods.clients.ado.workitems.AdoGetProjectWorkItemsClient.GetResponse')
    def test_single_repo_stats_activity(self, workitemsGetMock, workitemsPostMock, commentsMock, commitsByPrMock, commitsByRepoMock, prMock, entitlementsMock):
        workitemsGetMock.return_value.json.return_value = self.mockedWorkitemDetailsResponse
        workitemsPostMock.return_value.json.return_value = self.mockedWorkitemListResponse
        commentsMock.return_value.json.return_value = self.mockedPrThreadsResponse
        commitsByPrMock.return_value.json.return_value = self.mockedPrCommitsResponse
        commitsByRepoMock.return_value.json.return_value = self.mockedRepoCommitsResponse
        prMock.return_value.json.return_value = self.mockedRepoPrResponse
        entitlementsMock.return_value.json.return_value = self.mockedEntitlementReponse

        dataframe = self.clientManager.collectPullRequestActivity()
        self.assertEqual(len(dataframe), 54)

    @patch('gitinsights.mods.clients.ado.entitlements.AdoGetOrgEntitlementsClient.GetResponse')
    @patch('gitinsights.mods.clients.ado.pull_request.AdoPullRequestsClient.GetResponse')
    @patch('gitinsights.mods.clients.ado.commits.AdoPullRequestCommitsClient.GetCommitsByRepoResponse')
    @patch('gitinsights.mods.clients.ado.commits.AdoPullRequestCommitsClient.GetCommitsByPrResponse')
    @patch('gitinsights.mods.clients.ado.comments.AdoPullRequestReviewCommentsClient.GetResponse')
    @patch('gitinsights.mods.clients.ado.workitems.AdoGetProjectWorkItemsClient.PostResponse')
    @patch('gitinsights.mods.clients.ado.workitems.AdoGetProjectWorkItemsClient.GetResponse')
    def test_single_repo_stats_aggregate_activity(self, workitemsGetMock, workitemsPostMock, commentsMock, commitsByPrMock, commitsByRepoMock, prMock, entitlementsMock):
        workitemsGetMock.return_value.json.return_value = self.mockedWorkitemDetailsResponse
        workitemsPostMock.return_value.json.return_value = self.mockedWorkitemListResponse
        commentsMock.return_value.json.return_value = self.mockedPrThreadsResponse
        commitsByPrMock.return_value.json.return_value = self.mockedPrCommitsResponse
        commitsByRepoMock.return_value.json.return_value = self.mockedRepoCommitsResponse
        prMock.return_value.json.return_value = self.mockedRepoPrResponse
        entitlementsMock.return_value.json.return_value = self.mockedEntitlementReponse

        agg = self.clientManager.aggregatePullRequestActivity(['week'])

        self.assertEqual(len(agg), 1)
        self.assertEqual(agg.loc['44', 'prs_submitted'], 4)
        self.assertEqual(agg.loc['44', 'prs_merged'], 1)
        self.assertEqual(agg.loc['44', 'pr_completion_days'], 2)
        self.assertEqual(agg.loc['44', 'pr_comments'], 12)
        self.assertEqual(agg.loc['44', 'prs_reviewed'], 1)
        self.assertEqual(agg.loc['44', 'pr_commits_pushed'], 32)
        self.assertEqual(agg.loc['44', 'commit_change_count_additions'], 20)
        self.assertEqual(agg.loc['44', 'commit_change_count_edits'], 0)
        self.assertEqual(agg.loc['44', 'commit_change_count_deletes'], 12)
        self.assertEqual(agg.loc['44', 'user_stories_assigned'], 2)
        self.assertEqual(agg.loc['44', 'user_stories_completed'], 1)
        self.assertEqual(agg.loc['44', 'user_story_points_assigned'], 12)
        self.assertEqual(agg.loc['44', 'user_story_completion_days'], 1)
        self.assertEqual(agg.loc['44', 'user_stories_created'], 3)

    @patch('gitinsights.mods.clients.ado.entitlements.AdoGetOrgEntitlementsClient.GetResponse')
    @patch('gitinsights.mods.clients.ado.pull_request.AdoPullRequestsClient.GetResponse')
    @patch('gitinsights.mods.clients.ado.commits.AdoPullRequestCommitsClient.GetCommitsByRepoResponse')
    @patch('gitinsights.mods.clients.ado.commits.AdoPullRequestCommitsClient.GetCommitsByPrResponse')
    @patch('gitinsights.mods.clients.ado.comments.AdoPullRequestReviewCommentsClient.GetResponse')
    @patch('gitinsights.mods.clients.ado.workitems.AdoGetProjectWorkItemsClient.PostResponse')
    @patch('gitinsights.mods.clients.ado.workitems.AdoGetProjectWorkItemsClient.GetResponse')
    def test_multiple_repo_stats_aggregate_activity(self, workitemsGetMock, workitemsPostMock, commentsMock, commitsByPrMock, commitsByRepoMock, prMock, entitlementsMock):
        workitemsGetMock.return_value.json.return_value = self.mockedWorkitemDetailsResponse
        workitemsPostMock.return_value.json.return_value = self.mockedWorkitemListResponse
        commentsMock.return_value.json.return_value = self.mockedPrThreadsResponse
        commitsByPrMock.return_value.json.return_value = self.mockedPrCommitsResponse
        commitsByRepoMock.return_value.json.return_value = self.mockedRepoCommitsResponse
        prMock.return_value.json.return_value = self.mockedRepoPrResponse
        entitlementsMock.return_value.json.return_value = self.mockedEntitlementReponse
        self.clientManager.repos = ['repo1', 'repo2']

        agg = self.clientManager.aggregatePullRequestActivity(['week'])

        self.assertEqual(len(agg), 1)
        self.assertEqual(agg.loc['44', 'prs_submitted'], 8)
        self.assertEqual(agg.loc['44', 'prs_merged'], 2)
        self.assertEqual(agg.loc['44', 'pr_completion_days'], 2)
        self.assertEqual(agg.loc['44', 'pr_comments'], 24)
        self.assertEqual(agg.loc['44', 'prs_reviewed'], 2)
        self.assertEqual(agg.loc['44', 'pr_commits_pushed'], 64)
        self.assertEqual(agg.loc['44', 'commit_change_count_additions'], 40)
        self.assertEqual(agg.loc['44', 'commit_change_count_edits'], 0)
        self.assertEqual(agg.loc['44', 'commit_change_count_deletes'], 24)
        self.assertEqual(agg.loc['44', 'user_stories_assigned'], 2)
        self.assertEqual(agg.loc['44', 'user_stories_completed'], 1)
        self.assertEqual(agg.loc['44', 'user_story_points_assigned'], 12)
        self.assertEqual(agg.loc['44', 'user_story_completion_days'], 1)
        self.assertEqual(agg.loc['44', 'user_stories_created'], 3)
