import json
import os
from unittest import TestCase
from unittest.mock import Mock
from unittest.mock import patch

import pandas as pd

from gitinsights.mods.ado_client import AzureDevopsInsights


def loadMockFile(filePath: str):
    with open(os.path.join(os.path.dirname(__file__), filePath)) as f:
        return json.load(f)


def aggregateDataframe(df: pd.DataFrame) -> pd.DataFrame:
    return df.groupby(['week']) \
        .agg(
            {
                'prs_merged': 'sum',
                'prs_submitted': 'sum',
                'pr_completion_days': 'mean',
                'pr_comments': 'sum',
                'prs_reviewed': 'sum',
                'pr_commits_pushed': 'sum',
                'commit_change_count_edits': 'sum',
                'commit_change_count_deletes': 'sum',
                'commit_change_count_additions': 'sum',
                'user_stories_assigned': 'sum',
                'user_stories_completed': 'sum',
                'user_story_points_assigned': 'sum',
                'user_story_completion_days': 'mean',
                'user_stories_created': 'sum'
            })


class Test_ADOPrStatService(TestCase):
    def setUp(self):
        self.mockedRepoPrResponse = loadMockFile("./data/prStatsByProject.json")
        self.mockedPrThreadsResponse = loadMockFile("./data/prThreads.json")
        self.mockedPrCommitsResponse = loadMockFile("./data/prCommits.json")
        self.mockedRepoCommitsResponse = loadMockFile("./data/repoCommits.json")
        self.mockedWorkitemListResponse = loadMockFile("./data/workitemList.json")
        self.mockedWorkitemDetailsResponse = loadMockFile("./data/workitemDetails.json")

    @patch('gitinsights.mods.repo_insights_base.requests.get')
    def test_repo_pr_stats(self, mock_get):
        # Configuring the mock to return a response with an OK status code. Also, the mock should have
        # a `json()` method that returns a list of pr stats.

        mock_get.return_value = Mock(ok=True)
        mock_get.return_value.json.return_value = self.mockedRepoPrResponse
        client = AzureDevopsInsights("myorg", "my-super-project", ["repo1"], "team-buffalo")
        response = client.invokePRsByProjectAPICall("", "repo1")

        self.assertEqual(len(response), 4)

    @patch('gitinsights.mods.repo_insights_base.requests.get')
    def test_repo_pr_threads_stats(self, mock_get):
        # Configuring the mock to return a response with an OK status code. Also, the mock should have
        # a `json()` method that returns a list of pr threads.

        mock_get.return_value = Mock(ok=True)
        mock_get.return_value.json.return_value = self.mockedPrThreadsResponse
        client = AzureDevopsInsights("myorg", "my-super-project", ["repo1"], "team-buffalo")
        response = client.invokePRCommentThreadsAPICall("", "repo1", "1")

        self.assertEqual(len(response), 8)

    @patch.object(AzureDevopsInsights, 'invokeCommitsByRepoAPICall')
    def test_repo_commits_stats(self, commitsByRepoMock):
        emptyResponse = {"value": []}
        commitsByRepoMock.side_effect = [self.mockedRepoCommitsResponse['value'], emptyResponse['value']]
        client = AzureDevopsInsights("myorg", "my-super-project", ["repo1"], "team-buffalo")
        response = client.repoCommits("", "repo1")

        self.assertEqual(len(response), 8)
        self.assertEqual(response['3104bd0b0accbc74278fe6880e53215f6b93a5cd']['Add'], 1)
        self.assertEqual(response['9991b4f66def4c0a9ad8f9f27043ece7eddcf1c7']['Delete'], 1)

    @patch('gitinsights.mods.repo_insights_base.RepoInsightsClient.invokeAPICall')
    def test_invoke_workitem_api(self, invokeAPICallMock):
        invokeAPICallMock.side_effect = [self.mockedWorkitemListResponse['workItems'], self.mockedWorkitemDetailsResponse['value']]
        client = AzureDevopsInsights("myorg", "my-super-project", ["repo1"], "team-buffalo")
        response = client.invokeWorkitemsAPICall("", "team-buffalo")

        self.assertEqual(len(response), 3)

    @patch.object(AzureDevopsInsights, 'invokePRCommentThreadsAPICall')
    @patch.object(AzureDevopsInsights, 'invokePRsByProjectAPICall')
    @patch.object(AzureDevopsInsights, 'invokePRCommitsAPICall')
    @patch.object(AzureDevopsInsights, 'invokeCommitsByRepoAPICall')
    @patch.object(AzureDevopsInsights, 'invokeWorkitemsAPICall')
    def test_single_pr_stats_dataframe(self, workitemsMock, commitsByRepoMock, prCommits, prsByProject, prThreads):
        emptyResponse = {"value": []}
        commitsByRepoMock.side_effect = [self.mockedRepoCommitsResponse['value'], emptyResponse['value']]
        prThreads.return_value = self.mockedPrThreadsResponse['value']
        prsByProject.return_value = self.mockedRepoPrResponse['value']
        prCommits.return_value = self.mockedPrCommitsResponse['value']
        workitemsMock.return_value = self.mockedWorkitemDetailsResponse['value']
        expectedDataframeSize = 54
        client = AzureDevopsInsights("myorg", "my-super-project", ["repo1"], "team-buffalo")
        dataframe = client.collectPullRequestActivity("11c")
        self.assertEqual(len(dataframe), expectedDataframeSize)

        agg = aggregateDataframe(dataframe)

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

    @patch.object(AzureDevopsInsights, 'invokePRCommentThreadsAPICall')
    @patch.object(AzureDevopsInsights, 'invokePRsByProjectAPICall')
    @patch.object(AzureDevopsInsights, 'invokePRCommitsAPICall')
    @patch.object(AzureDevopsInsights, 'invokeCommitsByRepoAPICall')
    @patch.object(AzureDevopsInsights, 'invokeWorkitemsAPICall')
    def test_multiple_repo_pr_stats_dataframe(self, workitemsMock, commitsByRepoMock, prCommits, prsByProject, prThreads):
        emptyResponse = {"value": []}
        commitsByRepoMock.side_effect = [self.mockedRepoCommitsResponse['value'], emptyResponse['value'], self.mockedRepoCommitsResponse['value'], emptyResponse['value']]
        prThreads.return_value = self.mockedPrThreadsResponse['value']
        prsByProject.return_value = self.mockedRepoPrResponse['value']
        prCommits.return_value = self.mockedPrCommitsResponse['value']
        workitemsMock.return_value = self.mockedWorkitemDetailsResponse['value']
        repos = ["repo1", "repo2"]
        client = AzureDevopsInsights("myorg", "my-super-project", repos, "team-buffalo")
        dataframe = client.collectPullRequestActivity("11c")
        self.assertEqual(len(dataframe), 103)

        agg = aggregateDataframe(dataframe)

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

    @patch.object(AzureDevopsInsights, 'invokePRCommentThreadsAPICall')
    @patch.object(AzureDevopsInsights, 'invokePRsByProjectAPICall')
    @patch.object(AzureDevopsInsights, 'invokePRCommitsAPICall')
    @patch.object(AzureDevopsInsights, 'invokeCommitsByRepoAPICall')
    @patch.object(AzureDevopsInsights, 'invokeWorkitemsAPICall')
    def test_pr_activity_aggregation(self, workitemsMock, commitsByRepoMock, prCommits, prsByProject, prThreads):
        emptyResponse = {"value": []}
        commitsByRepoMock.side_effect = [self.mockedRepoCommitsResponse['value'], emptyResponse['value']]
        prThreads.return_value = self.mockedPrThreadsResponse['value']
        prsByProject.return_value = self.mockedRepoPrResponse['value']
        prCommits.return_value = self.mockedPrCommitsResponse['value']
        workitemsMock.return_value = self.mockedWorkitemDetailsResponse['value']
        client = AzureDevopsInsights("myorg", "my-super-project", ["repo1"], "team-buffalo")

        agg = client.aggregatePullRequestActivity(['week'], "11a")

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
