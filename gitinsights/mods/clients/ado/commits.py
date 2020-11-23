import logging
from typing import Dict
from typing import Iterator
from typing import List
from typing import Tuple

from dateutil import parser
from requests import Response

from ...managers.repo_insights_base import ApiClient
from ...managers.repo_insights_base import RepoInsightsManager


class AdoPullRequestCommitsClient(ApiClient):
    def __init__(self, organization: str, baseUrl: str, version: str, patToken: str, reportableFieldDefaults: dict):
        self.commitChangeCounts: Dict[str, dict] = {}
        super().__init__(organization, baseUrl, version, patToken, reportableFieldDefaults)

    @staticmethod
    def ParseRepoCommits(commits: List[dict]) -> Iterator[Tuple[str, dict]]:
        for commit in commits:
            yield commit['commitId'], commit['changeCounts']

    def getDeserializedDataset(self, **kwargs) -> List[dict]:
        required_args = {'repo', 'entitlements', 'pullRequestId', 'project'}
        RepoInsightsManager.checkRequiredKwargs(required_args, **kwargs)

        pullrequestId: str = kwargs['pullRequestId']
        entitlements: Dict[str, str] = kwargs['entitlements']
        repo: str = kwargs['repo']
        project: str = kwargs['project']
        uri_parameters: Dict[str, str] = {}

        commitsByPrResourcePath = "{}/{}/_apis/git/repositories/{}/pullrequests/{}/commits".format(self.organization, project, repo, pullrequestId)

        return self.DeserializeResponse(self.GetCommitsByPrResponse(commitsByPrResourcePath, uri_parameters), repo, project, entitlements)

    def GetCommitsByPrResponse(self, resourcePath: str, uri_parameters: Dict[str, str]) -> Response:
        return self.sendGetRequest(resourcePath, uri_parameters)

    def GetCommitsByRepoResponse(self, resourcePath: str, uri_parameters: Dict[str, str]) -> Response:
        return self.sendGetRequest(resourcePath, uri_parameters)

    def DeserializeResponse(self, response: Response, repo: str, project: str, entitlements: Dict[str, str]) -> List[dict]:
        recordList = []
        jsonResults = response.json()['value']

        # pre-load the commits by repo
        if repo not in self.commitChangeCounts:
            self.commitChangeCounts[repo] = self.getAllCommitsByRepo(repo, project)

        repoCommitChangeCounts = self.commitChangeCounts[repo]
        contributor: str

        if len(repoCommitChangeCounts) == 0:
            raise ValueError('Repo commit change counts are empty')

        for commit in filter(lambda c: 'commitId' in c and c['commitId'] in repoCommitChangeCounts, jsonResults):
            # If the author doesn't have their email configured within their local git profile
            if 'email' not in commit['author']:
                # search by author displayname
                authorAlias = {v: k for k, v in entitlements.items()}[commit['author']['name']].lower()
            else:
                authorAlias = commit['author']['email'].lower()

            # If the alias cannot be located in the registry then skip the commits from being included and ask the engineer to setup their local profile using their microsoft email.
            if authorAlias not in entitlements:
                logging.warning('Alias %s for commit %s has not contributed directly to any previous pull requests and cannot be found. Please configure the profileAliases setting with this commit email address.', authorAlias, commit['commitId'])
                contributor = authorAlias
            else:
                contributor = entitlements[authorAlias]

            recordList.append(
                {
                    **self.reportableFieldDefaults, **{
                        'contributor': contributor,
                        'week': parser.parse(commit['author']['date']).strftime("%V"),
                        'pr_commits_pushed': 1,
                        'commit_change_count_edits': repoCommitChangeCounts[commit['commitId']]['Edit'],
                        'commit_change_count_deletes': repoCommitChangeCounts[commit['commitId']]['Delete'],
                        'commit_change_count_additions': repoCommitChangeCounts[commit['commitId']]['Add'],
                        'repo': repo
                    }})

        return recordList

    def getAllCommitsByRepo(self, repo: str, project: str, topRecords: int = 400) -> Dict[str, dict]:
        new_results = True
        commitChangeCountDictionary: Dict[str, dict] = {}
        uri_parameters: Dict[str, str] = {}
        uri_parameters['searchCriteria.$skip'] = '0'
        uri_parameters['searchCriteria.$top'] = str(topRecords)

        commitsByRepoResourcePath = "{}/{}/_apis/git/repositories/{}/commits".format(self.organization, project, repo)
        page_count = 1

        while new_results:
            response = self.GetCommitsByRepoResponse(commitsByRepoResourcePath, uri_parameters).json()['value']
            commitChangeCountDictionary = {**dict(AdoPullRequestCommitsClient.ParseRepoCommits(response)), **commitChangeCountDictionary}
            new_results = len(response) == topRecords
            page_count += 1
            uri_parameters['searchCriteria.$skip'] = str(topRecords * page_count)

        return commitChangeCountDictionary
