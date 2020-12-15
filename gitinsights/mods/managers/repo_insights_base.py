import abc
from typing import Dict
from typing import List
from typing import Set

import pandas as pd
import requests
from dateutil import parser
from requests.adapters import HTTPAdapter
from requests.auth import HTTPBasicAuth
from urllib3.util.retry import Retry


# Base Class For Git Insights
class RepoInsightsManager(abc.ABC):
    def __init__(self, organization: str, project: str, repos: List[str], teamId: str, patToken: str, defaultEntitlements: Dict[str, str] = None):
        if defaultEntitlements is None:
            defaultEntitlements = {}

        self.organization: str = organization
        self.project: str = project
        self.repos: List[str] = repos
        self.teamId: str = teamId
        self.patToken = patToken
        self.defaultEntitlements = defaultEntitlements

        super().__init__()

    @staticmethod
    def dateStrDiffInDays(fromDate: str, toDate: str) -> float:
        if not fromDate or not toDate:
            raise ValueError('From and To Date are required')

        fromDatetime = parser.parse(fromDate)
        toDatetime = parser.parse(toDate)

        return (fromDatetime - toDatetime).days

    @staticmethod
    def checkRequiredKwargs(requiredKeys: Set[str], **kwargs):
        if not requiredKeys <= kwargs.keys():
            raise ValueError("missing required arguments exception: {}".format(requiredKeys))

    @abc.abstractmethod
    def _loadProjectEntitlements(self) -> Dict[str, str]:
        pass

    @abc.abstractmethod
    def _getRepoPullRequests(self, repo: str) -> List[dict]:
        raise NotImplementedError("Please Implement method getRepoPullRequests")

    @abc.abstractmethod
    def _getPullRequestCommits(self, **kwargs) -> List[dict]:
        raise NotImplementedError("Please Implement method getPullRequestCommits")

    @abc.abstractmethod
    def _getPullRequestComments(self, **kwargs) -> List[dict]:
        raise NotImplementedError("Please Implement method getPullRequestComments")

    @abc.abstractmethod
    def _getProjectWorkitems(self) -> List[dict]:
        raise NotImplementedError("Please Implement method getProjectWorkitems")

    @abc.abstractmethod
    def AggregationMeasures(self) -> dict:
        raise NotImplementedError("Please Implement method aggregationMeasures")

    def aggregatePullRequestActivity(self, groupByColumns: List[str]) -> pd.DataFrame:
        return self.collectPullRequestActivity().groupby(groupByColumns).agg(self.AggregationMeasures())

    def collectPullRequestActivity(self) -> pd.DataFrame:
        recordList = []

        if not self.repos:
            raise TypeError("Repo list is empty")

        if not self.patToken:
            raise TypeError("Unable to resolve the PAT token: {}".format(self.patToken))

        entitlements = {**self._loadProjectEntitlements(), **self.defaultEntitlements}

        for repo in self.repos:
            pullRequests = self._getRepoPullRequests(repo)
            recordList.extend(pullRequests)

            for pr in [filtered_pr for filtered_pr in pullRequests if filtered_pr['prs_submitted'] == 1]:
                recordList.extend(self._getPullRequestCommits(entitlements=entitlements, pullRequest=pr, repo=repo))
                recordList.extend(self._getPullRequestComments(pullRequest=pr, repo=repo))

        recordList.extend(self._getProjectWorkitems())

        return pd.DataFrame(recordList)


class ApiClient(abc.ABC):
    # pylint: disable=too-many-instance-attributes
    def __init__(self, organization: str, baseUrl: str, version: str, patToken: str, reportableFieldDefaults: dict, retry_count: int = 3, retry_backoff_factor: float = 1, default_timeout: float = 5):
        self.organization: str = organization
        self.baseUrl = baseUrl.lstrip('https://')
        self.version = version
        self.reportableFieldDefaults = reportableFieldDefaults
        self.patToken = patToken
        self.retry_status_force_response_codes = [429, 500, 502, 503, 504]
        self.retry_count = retry_count
        self.retry_backoff_factor = retry_backoff_factor
        self.default_timeout = default_timeout

    def uri(self, resourcePath: str, parameters: Dict[str, str]) -> str:
        uri_str = "https://{}/{}?".format(self.baseUrl, resourcePath)
        if 'api-version' not in parameters:
            parameters['api-version'] = self.version

        for i, (paramName, value) in enumerate(parameters.items()):
            delimiter = "&" if not i == 0 else ""
            uri_str += "{}{}={}".format(delimiter, paramName, value)

        return uri_str

    def requests_retry_session(self, session: requests.Session = None) -> requests.Session:
        session = session or requests.Session()
        retry = Retry(
            total=self.retry_count,
            read=self.retry_count,
            connect=self.retry_count,
            backoff_factor=self.retry_backoff_factor,
            status_forcelist=self.retry_status_force_response_codes
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)

        return session

    def sendGetRequest(self, resourcePath: str, parameters: Dict[str, str]) -> requests.Response:
        return self.requests_retry_session()\
            .get(self.uri(resourcePath, parameters), auth=HTTPBasicAuth('', self.patToken), timeout=self.default_timeout)

    def sendPostRequest(self, resourcePath: str, postBody: Dict[str, str], parameters: Dict[str, str]) -> requests.Response:
        return self.requests_retry_session()\
            .post(self.uri(resourcePath, parameters), json=postBody, auth=HTTPBasicAuth('', self.patToken), timeout=self.default_timeout)

    @abc.abstractmethod
    def getDeserializedDataset(self, **kwargs) -> List[dict]:
        raise NotImplementedError("Please Implement method deserializeResponse")
