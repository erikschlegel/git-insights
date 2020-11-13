import abc
from typing import Dict
from typing import List

import pandas as pd
import requests
from dateutil import parser
from requests.auth import HTTPBasicAuth


# Base Class For Git Insights
class RepoInsightsClient(abc.ABC):
    def __init__(self, organization: str, project: str, repos: List[str], teamId: str, profileAliases: Dict[str, str] = None):
        if profileAliases is None:
            profileAliases = {}

        self.organization: str = organization
        self.project: str = project
        self.repos: List[str] = repos
        self.teamId: str = teamId
        self.profileIdentityAliases = profileAliases
        self.commitChangeCounts: Dict[str, dict] = {}

        super().__init__()

    @staticmethod
    def dateStrDiffInDays(fromDate: str, toDate: str) -> float:
        if not fromDate or not toDate:
            raise ValueError('From and To Date are required')

        fromDatetime = parser.parse(fromDate)
        toDatetime = parser.parse(toDate)

        return (fromDatetime - toDatetime).days

    @staticmethod
    def invokeAPICall(patToken: str, uri: str, responseValueProperty: str = 'value', method: str = "GET", postBody: Dict[str, str] = None) -> List[dict]:
        response = None

        if method == "GET":
            response = requests.get(uri, auth=HTTPBasicAuth('', patToken))
        elif method == "POST":
            response = requests.post(uri, json=postBody, auth=HTTPBasicAuth('', patToken))
        else:
            raise TypeError(f"method: {method} is unsupported.")

        return response.json()[responseValueProperty]

    @abc.abstractmethod
    def ParsePullRequest(self, pullrequest: dict) -> List[dict]:
        raise NotImplementedError("Please Implement method parsePullRequest")

    @abc.abstractmethod
    def ParsePullRequestComments(self, comments: List[dict], repo: str) -> List[dict]:
        raise NotImplementedError("Please Implement method parsePullRequestComments")

    @abc.abstractmethod
    def ParsePullRequestCommits(self, commits: List[dict], patToken: str, repo: str) -> List[dict]:
        raise NotImplementedError("Please Implement method parsePullRequestCommits")

    @abc.abstractmethod
    def ParseWorkitems(self, repo: str, workitems: List[dict]) -> List[dict]:
        raise NotImplementedError("Please Implement method parseWorkitems")

    @abc.abstractmethod
    def invokeWorkitemsAPICall(self, patToken: str, teamID: str) -> List[dict]:
        raise NotImplementedError("Please Implement method invokeWorkitemsAPICall")

    @abc.abstractmethod
    def AggregationMeasures(self) -> dict:
        raise NotImplementedError("Please Implement method aggregationMeasures")

    @abc.abstractmethod
    def invokePRsByProjectAPICall(self, patToken: str, repo: str) -> List[dict]:
        raise NotImplementedError("Please Implement method invokePRsByProjectAPICall")

    @abc.abstractmethod
    def invokePRCommentThreadsAPICall(self, patToken: str, repoID: str, prID: str) -> List[dict]:
        raise NotImplementedError("Please Implement method invokePRCommentThreadsAPICall")

    @abc.abstractmethod
    def invokePRCommitsAPICall(self, patToken: str, repoID: str, prID: str) -> List[dict]:
        raise NotImplementedError("Please Implement method invokePRCommitsAPICall")

    def aggregatePullRequestActivity(self, groupByColumns: List[str], patToken: str) -> pd.DataFrame:
        return self.collectPullRequestActivity(patToken) \
            .groupby(groupByColumns) \
            .agg(self.AggregationMeasures())

    def collectPullRequestActivity(self, patToken: str) -> pd.DataFrame:
        recordList = []

        if not self.repos:
            raise TypeError("Repo list is empty")

        if not patToken:
            raise TypeError("Unable to resolve the PAT token: {}".format(patToken))

        for repo in self.repos:
            rsp = self.invokePRsByProjectAPICall(patToken, repo)

            for _, pr in pd.DataFrame.from_dict(rsp).iterrows():
                commentsRsp = self.invokePRCommentThreadsAPICall(patToken, pr['repository']['id'], pr['pullRequestId'])
                commitsRsp = self.invokePRCommitsAPICall(patToken, pr['repository']['id'], pr['pullRequestId'])
                recordList += self.ParsePullRequest(pr) + self.ParsePullRequestCommits(commitsRsp, patToken, repo)
                for comments in commentsRsp:
                    recordList += self.ParsePullRequestComments(comments['comments'], repo)

        workitemResponse = self.invokeWorkitemsAPICall(patToken, self.teamId)
        recordList += self.ParseWorkitems(self.repos[0], workitemResponse)

        return pd.DataFrame(recordList)
