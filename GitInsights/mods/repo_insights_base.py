import abc
import logging
import pandas as pd
import requests

from dateutil import parser
from requests.auth import HTTPBasicAuth

class RepoInsightsClient(abc.ABC):
    def __init__(self, organization: str, project: str, repos: [str], teamId: str, profileAliases: dict = {}):
        self.organization: str = organization
        self.project: str = project
        self.repos: [str] = repos
        self.teamId: str = teamId
        self.profileIdentityAliases = profileAliases

        super().__init__()

    @staticmethod
    def dateStrDiffInDays(fromDate: str, toDate: str) -> float:
        if fromDate and toDate:
            fromDatetime = parser.parse(fromDate)
            toDatetime = parser.parse(toDate)

            return (fromDatetime - toDatetime).days
        else:
            return None

    @abc.abstractmethod
    def parsePullRequest(self, pullrequest: [dict]) -> [dict]:
        raise NotImplementedError("Please Implement method parsePullRequest")

    @abc.abstractmethod
    def parsePullRequestComments(self, comments: [dict], repo: str) -> [dict]:
        raise NotImplementedError("Please Implement method parsePullRequestComments")

    @abc.abstractmethod
    def parsePullRequestCommits(self, commits: [dict], repo: str) -> [dict]:
        raise NotImplementedError("Please Implement method parsePullRequestCommits")

    @abc.abstractmethod
    def parseWorkitems(self, repo: str, workitems: [dict]) -> [dict]:
        raise NotImplementedError("Please Implement method parseWorkitems")

    @abc.abstractmethod
    def invokeWorkitemsAPICall(self, patToken: str, teamID: str) -> [dict]:
        raise NotImplementedError("Please Implement method invokeWorkitemsAPICall")

    @abc.abstractmethod
    def aggregationMeasures(self) -> dict:
        raise NotImplementedError("Please Implement method aggregationMeasures")

    @abc.abstractmethod
    def invokePRsByProjectAPICall(self, patToken: str, repo: str) -> [dict]:
        raise NotImplementedError("Please Implement method invokePRsByProjectAPICall")
    
    @abc.abstractmethod
    def invokePRCommentThreadsAPICall(self, patToken: str, repoID: str, prID: str) -> [dict]:
        raise NotImplementedError("Please Implement method invokePRCommentThreadsAPICall")

    @abc.abstractmethod
    def invokePRCommitsAPICall(self, patToken: str, repoID: str, prID: str) -> [dict]:
        raise NotImplementedError("Please Implement method invokePRCommitsAPICall")

    def invokeAPICall(self, patToken: str, uri: str, responseValueProperty: str = 'value', method: str = "GET", postBody: dict = {}) -> [dict]:
        response = None

        if method == "GET":
            response = requests.get(uri, auth=HTTPBasicAuth('', patToken))
        elif method == "POST":
            response = requests.post(uri, json=postBody, auth=HTTPBasicAuth('', patToken))
        else:
            raise TypeError(f"method: {method} is unsupported.")

        return response.json()[responseValueProperty]

    def aggregatePullRequestActivity(self, groupByColumns: [str], patToken: str) -> pd.DataFrame:
        return self.collectPullRequestActivity(patToken) \
            .groupby(groupByColumns) \
            .agg(self.aggregationMeasures)

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
                recordList += self.parsePullRequest(pr) + self.parsePullRequestCommits(commitsRsp, patToken, repo)
                for comments in commentsRsp:
                    recordList += self.parsePullRequestComments(comments['comments'], repo)

        workitemResponse = self.invokeWorkitemsAPICall(patToken, self.teamId)
        recordList += self.parseWorkitems(repo, workitemResponse)

        return pd.DataFrame(recordList)
