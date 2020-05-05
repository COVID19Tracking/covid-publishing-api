"""
RestTester -- a support class for running test queries against a REST API.

Support a base URL and an optional access key (currently a bearer cert)

"""
from typing import Dict, Tuple
import requests
import pytest
from loguru import logger
import json


class RestTester:

    def __init__(self, api_url: str, trace=False, offer_infrastructure_api_key: str = None):
        self.api_url = api_url
        self.trace = trace
        self.verify = 'localhost' not in api_url
        self.offer_infrastructure_api_key = offer_infrastructure_api_key


    @property
    def auth_header(self) -> Dict:
        " add a Bearer certificate to the API call "
        if self.offer_infrastructure_api_key is not None:
            return {"Authorization": "Bearer " + self.offer_infrastructure_api_key}
        else:
            return None

    def get(self, sub_url: str):
        """ 
        perform a GET, returns a parsed json object
        throws exception on error status code or bad json response
        """
        url = self.api_url + sub_url
        resp = requests.get(url, verify=self.verify)
        if resp.status_code > 299:
            pytest.fail(f"get {url} failed: {resp.status_code} {resp.content}")

        if self.is_html(resp.content):
            logger.error("endpoint returned HTML, not json")
            pytest.fail(f"get {url} failed: endpoint returned HTML, not json")

        if self.trace:
            logger.info(f"get {url} returned: {resp.content}")

        try:
            x = resp.json()
            return x
        except Exception as ex:
            if not self.trace:
                logger.info(f"get {url} returned: {resp.content}")
            logger.error(f"json deserialization failed: {ex}")
            pytest.fail(f"get {url} failed: could not deserialize response")

    def get_with_status(self, sub_url: str) -> Tuple[int, str]:
        """ 
        perform a GET, returns status and response content as a string
        """
        url = self.api_url + sub_url
        resp = requests.get(url)
        # if resp.status_code <= 299:
        #    pytest.fail(f"get w/failure {url} did not fail: {resp.status_code} {resp.content}")

        if self.trace:
            logger.info(f"get w/status {url} returned: {resp.status_code} {resp.content}")
        return (resp.status_code, resp.content)

    def post(self, sub_url: str, json=None):
        """ 
        perform a POST, returns a parsed json object
        throws exception on error status code or bad json response
        """
        url = self.api_url + sub_url

        if self.trace:
            logger.info(f"post {url} with data = {json.dumps(json)}")

        resp = requests.post(url, json=json, verify=self.verify, headers=self.auth_header)
        if resp.status_code > 299:
            pytest.fail(f"post {url} failed: {resp.status_code} {resp.content}")

        if self.is_html(resp.content):
            logger.error("endpoint returned HTML, not json")
            pytest.fail(f"get {url} failed: endpoint returned HTML, not json")

        if self.trace:
            logger.info(f"post {url} returned: {resp.content}")

        try:
            x = resp.json()
            return x
        except Exception as ex:
            if not self.trace:
                logger.info(f"post {url} with data = {json.dumps(json)}")
                logger.info(f"post {url} returned: {resp.content}")
            logger.error(f"json deserialization failed: {ex}")
            pytest.fail(f"post {url} failed: could not deserialize response")

    def post_with_status(self, sub_url: str, json=None) -> Tuple[int, str]:
        """ 
        perform a POST, returns status and response content as a string
        """
        url = self.api_url + sub_url

        if self.trace:
            logger.info(f"post w/status {url} with data = {json.dumps(json)}")

        resp = requests.post(url, json=json)
        if resp.status_code < 300:
            pytest.fail(f"post w/failure {url} did not fail: {resp.status_code} {resp.content}")

        if self.trace:
            logger.info(f"post w/status {url} returned: {resp.status_code} {resp.content}")

        return (resp.status_code, resp.content)

    def delete(self, sub_url: str):
        """ 
        perform a DELETE, returns parsed JSON
        throws exception on error status code or bad json response
        """
        url = self.api_url + sub_url

        if self.trace:
            logger.info(f"delete {url}")

        resp = requests.delete(url)
        if resp.status_code > 299:
            pytest.fail(f"delete {url} failed: {resp.status_code} {resp.content}")

        if self.is_html(resp.content):
            logger.error("endpoint returned HTML, not json")
            pytest.fail(f"get {url} failed: endpoint returned HTML, not json")

        if self.trace:
            logger.info(f"delete {url} returned: {resp.content}")

        try:
            x = resp.json()
            return x
        except Exception as ex:
            if not self.trace:
                logger.info(f"delete {url} returned: {resp.content}")
            logger.error(f"json deserialization failed: {ex}")
            pytest.fail(f"delete {url} failed: could not deserialize response")

    def is_html(self, bcontent: bytes) -> bool:
        " tests if content is HTML, not json"
        content = str(bcontent)
        if "<html" in content: return True
        if "<body" in content: return True
        return False
