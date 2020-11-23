
from typing import Dict
from typing import List

import numpy as np

from ...mods.clients.ado.comments import AdoPullRequestReviewCommentsClient
from ...mods.clients.ado.commits import AdoPullRequestCommitsClient
from ...mods.clients.ado.entitlements import AdoGetOrgEntitlementsClient
from ...mods.clients.ado.pull_request import AdoPullRequestsClient
from ...mods.clients.ado.workitems import AdoGetProjectWorkItemsClient
from ...mods.managers.repo_insights_base import RepoInsightsManager

BASE_URI = 'dev.azure.com'
DEFAULT_VERSION = '6.0'


class AzureDevopsClientManager(RepoInsightsManager):
    def __init__(self, organization: str, project: str, repos: List[str], teamId: str, patToken: str, profileAliases: Dict[str, str] = None):
        self.pullrequestClient = AdoPullRequestsClient(organization, BASE_URI, DEFAULT_VERSION, patToken, self._reportableFieldDefaults)
        self.commitsByPullrequestClient = AdoPullRequestCommitsClient(organization, BASE_URI, DEFAULT_VERSION, patToken, self._reportableFieldDefaults)
        self.pullRequestCommentsClient = AdoPullRequestReviewCommentsClient(organization, BASE_URI, DEFAULT_VERSION, patToken, self._reportableFieldDefaults)
        self.entitlementsClient = AdoGetOrgEntitlementsClient(organization, 'vssps.dev.azure.com', '5.1-preview.1', patToken, self._reportableFieldDefaults)
        self.workitemsClient = AdoGetProjectWorkItemsClient(organization, BASE_URI, DEFAULT_VERSION, patToken, self._reportableFieldDefaults)

        super().__init__(organization, project, repos, teamId, patToken, profileAliases)

    @property
    def _reportableFields(self) -> Dict[str, dict]:
        return {
                'contributor': {'default': np.nan, 'agg_function': None},
                'prs_submitted': {'default': 0, 'agg_function': 'sum'},
                'prs_merged': {'default': 0, 'agg_function': 'sum'},
                'week': {'default': np.nan, 'agg_function': None},
                'prs_reviewed': {'default': 0, 'agg_function': 'sum'},
                'pr_comments': {'default': 0, 'agg_function': 'sum'},
                'creation_datetime': {'default': np.nan, 'agg_function': None},
                'pr_commits_pushed': {'default': 0, 'agg_function': 'sum'},
                'commit_change_count_edits': {'default': 0, 'agg_function': 'sum'},
                'commit_change_count_deletes': {'default': 0, 'agg_function': 'sum'},
                'commit_change_count_additions': {'default': 0, 'agg_function': 'sum'},
                'completion_date': {'default': np.nan, 'agg_function': None},
                'pr_completion_days': {'default': np.nan, 'agg_function': 'mean'},
                'repo': {'default': np.nan, 'agg_function': None},
                'user_stories_assigned': {'default': 0, 'agg_function': 'sum'},
                'user_stories_completed': {'default': 0, 'agg_function': 'sum'},
                'user_story_points_assigned': {'default': 0, 'agg_function': 'sum'},
                'user_story_points_completed': {'default': 0, 'agg_function': 'sum'},
                'user_story_completion_days': {'default': np.nan, 'agg_function': 'mean'},
                'user_stories_created': {'default': 0, 'agg_function': 'sum'}
            }

    @property
    def _reportableFieldDefaults(self) -> dict:
        return {k: v['default'] for k, v in self._reportableFields.items()}

    def AggregationMeasures(self) -> dict:
        return {k: v['agg_function'] for k, v in self._reportableFields.items() if v['agg_function'] is not None}

    def _getRepoPullRequests(self, repo: str = None) -> List[dict]:
        return self.pullrequestClient.getDeserializedDataset(repo=repo, project=self.project)

    def _getPullRequestCommits(self, **kwargs) -> List[dict]:
        RepoInsightsManager.checkRequiredKwargs({'repo', 'entitlements', 'pullRequest'}, **kwargs)
        repo = kwargs['repo']
        entitlements = kwargs['entitlements']
        pullRequestId = kwargs['pullRequest']['pullRequestId']

        return self.commitsByPullrequestClient.getDeserializedDataset(repo=repo, project=self.project, entitlements=entitlements, pullRequestId=pullRequestId)

    def _getPullRequestComments(self, **kwargs) -> List[dict]:
        RepoInsightsManager.checkRequiredKwargs({'repo', 'pullRequest'}, **kwargs)
        pullrequestId = kwargs['pullRequest']['pullRequestId']
        repo = kwargs['repo']

        return self.pullRequestCommentsClient.getDeserializedDataset(project=self.project, repo=repo, pullRequestId=pullrequestId)

    def _getProjectWorkitems(self) -> List[dict]:
        if self.teamId is None or self.project is None:
            raise ValueError('required arguments missing exception: teamId, project')

        if len(self.repos) == 0:
            return []

        return self.workitemsClient.getDeserializedDataset(teamId=self.teamId, project=self.project, repo=self.repos[0])

    def _loadProjectEntitlements(self) -> Dict[str, str]:
        entitlementsList = self.entitlementsClient.getDeserializedDataset()

        return entitlementsList[0] if len(entitlementsList) > 0 else {}
