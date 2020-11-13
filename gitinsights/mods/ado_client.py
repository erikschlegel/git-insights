import logging
from enum import Enum
from typing import Dict
from typing import Iterator
from typing import List
from typing import Tuple

import numpy as np
from dateutil import parser

from .repo_insights_base import RepoInsightsClient


class PullRequestVoteStatus(Enum):
    APPROVED = 10
    APPROVED_WITH_SUGGESTIONS = 5


class AzureDevopsInsights(RepoInsightsClient):
    def AggregationMeasures(self) -> dict:
        return {
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
                'user_story_points_completed': 'sum',
                'user_story_completion_days': 'mean',
                'user_stories_created': 'sum'
        }

    @property
    def ReportableFieldsDefault(self) -> dict:
        return {
                'contributor': np.nan,
                'prs_submitted': 0,
                'prs_merged': 0,
                'week': np.nan,
                'prs_reviewed': 0,
                'pr_comments': 0,
                'creation_datetime': np.nan,
                'pr_commits_pushed': 0,
                'commit_change_count_edits': 0,
                'commit_change_count_deletes': 0,
                'commit_change_count_additions': 0,
                'completion_date': np.nan,
                'pr_completion_days': np.nan,
                'repo': np.nan,
                'user_stories_assigned': 0,
                'user_stories_completed': 0,
                'user_story_points_assigned': 0,
                'user_story_points_completed': 0,
                'user_story_completion_days': np.nan,
                'user_stories_created': 0
            }

    @staticmethod
    def mergeDictionaries(dict1, dict2) -> dict:
        return {**dict2, **dict1}

    @staticmethod
    def ParseRepoCommits(commits: List[dict]) -> Iterator[Tuple[str, dict]]:
        for commit in commits:
            yield commit['commitId'], commit['changeCounts']

    def prCommentThreadsURI(self, repo: str, prID: str) -> str:
        uriFormat = 'https://dev.azure.com/{}/{}/_apis/git/repositories/{}/pullrequests/{}/threads?api-version=6.0'

        return uriFormat.format(self.organization, self.project, repo, prID)

    def repoPullRequestsURI(self, repo: str) -> str:
        uriFormat = 'https://dev.azure.com/{}/{}/_apis/git/repositories/{}/pullrequests?searchCriteria.status={}&api-version=6.0'
        prStatusFilter: str = "all"

        return uriFormat.format(self.organization, self.project, repo, prStatusFilter)

    def repoCommitsURI(self, repo: str, topRecords: int, skippedRecords: int) -> str:
        uriFormat = 'https://dev.azure.com/{}/{}/_apis/git/repositories/{}/commits?&searchCriteria.$skip={}&searchCriteria.$top={}&api-version=6.0'

        return uriFormat.format(self.organization, self.project, repo, skippedRecords, topRecords)

    def repoPrCommitsURI(self, repo: str, prID: str) -> str:
        uriFormat = 'https://dev.azure.com/{}/{}/_apis/git/repositories/{}/pullrequests/{}/commits?api-version=6.0'

        return uriFormat.format(self.organization, self.project, repo, prID)

    def listWorkitemIdsURI(self, teamId: str) -> str:
        uriFormat = 'https://dev.azure.com/{}/{}/{}/_apis/wit/wiql?api-version=6.0'

        return uriFormat.format(self.organization, self.project, teamId)

    def getWorkitemDetailsURI(self, workItemIds: List[str]) -> str:
        if len(workItemIds) > 200:
            raise SystemError('The workitems API only supports up to 200 items for a single call.')

        uriFormat = 'https://dev.azure.com/{}/{}/_apis/wit/workitems?ids={}&api-version=6.0'

        return uriFormat.format(self.organization, self.project, ','.join(workItemIds))

    def invokePRCommentThreadsAPICall(self, patToken: str, repoID: str, prID: str) -> List[dict]:
        return RepoInsightsClient.invokeAPICall(patToken, self.prCommentThreadsURI(repoID, prID))

    def invokePRCommitsAPICall(self, patToken: str, repoID: str, prID: str) -> List[dict]:
        return RepoInsightsClient.invokeAPICall(patToken, self.repoPrCommitsURI(repoID, prID))

    def invokePRsByProjectAPICall(self, patToken: str, repo: str) -> List[dict]:
        return RepoInsightsClient.invokeAPICall(patToken, self.repoPullRequestsURI(repo))

    def invokeWorkitemsAPICall(self, patToken: str, teamID: str) -> List[dict]:
        wiQLQuery = "Select [System.Id] From WorkItems Where [System.WorkItemType] = 'User Story' AND [State] <> 'Removed'"
        workitemListResponse = RepoInsightsClient.invokeAPICall(patToken, self.listWorkitemIdsURI(teamID), 'workItems', "POST", {"query": wiQLQuery})
        workItemDetails = []
        recordsProcessed = 0
        topElements = 200

        while recordsProcessed < len(workitemListResponse):
            workItemDetails += self.invokeGetWorkitemDetailsAPICall(patToken, [str(w['id']) for w in workitemListResponse[recordsProcessed:topElements+recordsProcessed]])
            recordsProcessed += topElements

        return workItemDetails

    def ParseWorkitems(self, repo: str, workitems: List[dict]) -> List[dict]:
        recordList = []

        for workitem in workitems:
            recordList.append(
                AzureDevopsInsights.mergeDictionaries(
                    {
                        'contributor': workitem['fields']['System.CreatedBy']['displayName'],
                        'week': parser.parse(workitem['fields']['System.CreatedDate']).strftime("%V"),
                        'repo': repo,
                        'user_stories_created': 1
                    }, self.ReportableFieldsDefault))

            if {'Microsoft.VSTS.Common.ActivatedDate', 'System.AssignedTo'} <= set(workitem['fields']) and workitem['fields']['System.State'] != 'New':
                recordList.append(
                    AzureDevopsInsights.mergeDictionaries(
                        {
                            'contributor': workitem['fields']['System.AssignedTo']['displayName'],
                            'week': parser.parse(workitem['fields']['Microsoft.VSTS.Common.ActivatedDate']).strftime("%V"),
                            'repo': repo,
                            'user_stories_assigned': 1,
                            'user_stories_completed': 1 if workitem['fields']['System.State'] in ['Closed', 'Resolved'] else 0,
                            'user_story_points_completed': workitem['fields']['Microsoft.VSTS.Scheduling.StoryPoints'] if workitem['fields']['System.State'] in ['Closed', 'Resolved'] and 'Microsoft.VSTS.Scheduling.StoryPoints' in workitem['fields'] else 0,
                            'user_story_points_assigned': workitem['fields']['Microsoft.VSTS.Scheduling.StoryPoints'] if 'Microsoft.VSTS.Scheduling.StoryPoints' in workitem['fields'] else 0,
                            'user_story_completion_days': RepoInsightsClient.dateStrDiffInDays(workitem['fields']['Microsoft.VSTS.Common.ResolvedDate'], workitem['fields']['Microsoft.VSTS.Common.ActivatedDate']) if workitem['fields']['System.State'] in ['Closed', 'Resolved'] else np.nan
                        }, self.ReportableFieldsDefault))

        return recordList

    def invokeGetWorkitemDetailsAPICall(self, patToken: str, workItemIds: List[str]) -> List[dict]:
        return RepoInsightsClient.invokeAPICall(patToken, self.getWorkitemDetailsURI(workItemIds))

    def invokeCommitsByRepoAPICall(self, patToken: str, repo: str, topRecords: int, skippedRecords: int) -> List[dict]:
        return RepoInsightsClient.invokeAPICall(patToken, self.repoCommitsURI(repo, topRecords, skippedRecords))

    def repoCommits(self, patToken: str, repo: str, topRecords: int = 400) -> dict:
        new_results = True
        commitChangeCountDictionary: Dict[str, dict] = {}
        page_count = 1

        while new_results:
            response = self.invokeCommitsByRepoAPICall(patToken, repo, topRecords, topRecords * page_count)
            commitChangeCountDictionary = {**dict(AzureDevopsInsights.ParseRepoCommits(response)), **commitChangeCountDictionary}
            new_results = len(response) > 0
            page_count += 1

        return commitChangeCountDictionary

    # We need to maintain a registry of contributor profiles to account for local git profile <> ADO profile discrepencies
    def addProfileAliasToRegistry(self, uniqueProfileId: str, displayName: str) -> None:
        if uniqueProfileId.lower() not in self.profileIdentityAliases:
            self.profileIdentityAliases[uniqueProfileId.lower()] = displayName

    def ParsePullRequest(self, pullrequest: dict) -> List[dict]:
        recordList = []
        self.addProfileAliasToRegistry(pullrequest['createdBy']['uniqueName'], pullrequest['createdBy']['displayName'])

        recordList.append(
            AzureDevopsInsights.mergeDictionaries(
                {
                    'contributor': pullrequest['createdBy']['displayName'],
                    'prs_submitted': 1,
                    'prs_merged': 1 if pullrequest['status'] == 'completed' else 0,
                    'week': parser.parse(pullrequest['creationDate']).strftime("%V"),
                    'creation_datetime': parser.parse(pullrequest['creationDate']),
                    'completion_date': parser.parse(pullrequest['closedDate']) if pullrequest['status'] == 'completed' else np.nan,
                    'pr_completion_days': RepoInsightsClient.dateStrDiffInDays(pullrequest['closedDate'], pullrequest['creationDate']) if pullrequest['status'] == 'completed' else np.nan,
                    'repo': pullrequest['repository']['name']
                }, self.ReportableFieldsDefault))

        for review in filter(lambda rv: rv['vote'] in [PullRequestVoteStatus.APPROVED.value, PullRequestVoteStatus.APPROVED_WITH_SUGGESTIONS.value] and 'isContainer' not in rv, pullrequest['reviewers']):
            self.addProfileAliasToRegistry(review['uniqueName'], review['displayName'])

            recordList.append(
                AzureDevopsInsights.mergeDictionaries(
                    {
                        'contributor': review['displayName'],
                        'week': parser.parse(pullrequest['creationDate']).strftime("%V"),
                        'prs_reviewed': 1,
                        'repo': pullrequest['repository']['name']
                    }, self.ReportableFieldsDefault))

        return recordList

    def ParsePullRequestComments(self, comments: List[dict], repo: str) -> List[dict]:
        recordList = []

        for comment in filter(lambda c: c['commentType'] != 'system', comments):
            recordList.append(
                AzureDevopsInsights.mergeDictionaries(
                    {
                        'contributor': comment['author']['displayName'],
                        'week': parser.parse(comment['lastUpdatedDate']).strftime("%V"),
                        'pr_comments': 1,
                        'repo': repo
                    }, self.ReportableFieldsDefault))

        return recordList

    def ParsePullRequestCommits(self, commits: List[dict], patToken: str, repo: str) -> List[dict]:
        recordList = []

        if repo not in self.commitChangeCounts:
            self.commitChangeCounts[repo] = self.repoCommits(patToken, repo)

        repoCommitChangeCounts = self.commitChangeCounts[repo]

        if len(repoCommitChangeCounts) == 0:
            raise ValueError('Repo commit change counts are empty')

        for commit in filter(lambda c: c['commitId'] in repoCommitChangeCounts, commits):
            # If the author doesn't have their email configured within their local git profile
            if 'email' not in commit['author']:
                # search by author displayname
                authorAlias = {v: k for k, v in self.profileIdentityAliases.items()}[commit['author']['name']].lower()
            else:
                authorAlias = commit['author']['email'].lower()

            # If the alias cannot be located in the registry then skip the commits from being included and ask the engineer to setup their local profile using their microsoft email.
            if authorAlias not in self.profileIdentityAliases:
                logging.warning('Alias %s for commit %s has not contributed directly to any previous pull requests and cannot be found', authorAlias, commit['commitId'])
                continue

            recordList.append(
                AzureDevopsInsights.mergeDictionaries(
                    {
                        'contributor': self.profileIdentityAliases[authorAlias],
                        'week': parser.parse(commit['author']['date']).strftime("%V"),
                        'pr_commits_pushed': 1,
                        'commit_change_count_edits': repoCommitChangeCounts[commit['commitId']]['Edit'],
                        'commit_change_count_deletes': repoCommitChangeCounts[commit['commitId']]['Delete'],
                        'commit_change_count_additions': repoCommitChangeCounts[commit['commitId']]['Add'],
                        'repo': repo
                    }, self.ReportableFieldsDefault))

        return recordList
