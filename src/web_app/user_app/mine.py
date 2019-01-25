# mine_json.py
# Written by Stephen White
# Date: 9/14/2018
# Purpose: Quickly demonstrate how to mine and download a JSON file from the
#          GitHub API.

import requests # needed to make an outgoing request to the API
from requests.auth import HTTPBasicAuth # Needed to be validated by GitHub
import json


# Without these, GitHub will see the request is being made by a python script
# and we will get a '403,' which means forbidden.
HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) \
            AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

# If you wish to use a proxy, fill this out
PROXIES = {'http': 'http://<username>:<password>@107.182....:<port>'}

# A specific payload for a pull request
PULL_PAYLOAD = {'page': '1', 'per_page': '100','sort': 'created', 'order': 'desc'}

# This will be the base url and repo that we will be working with, but we need to append some things to it
REQUEST_URL, REPO = "https://api.github.com/repos/", "rails/rails"


# Replace with your username, and your password/generated OAuth Token.
# This info will be used to authorize your account upon making a request.
GITHUB_USERNAME, GITHUB_AUTH = "Swhite9478", "f9bcbd6a947489591b52946bd592d4ff5a31152f"


# Function that will download a pull request json file from  a specified repo
def download_api_page_json(pull_num):
    api_url = REQUEST_URL + REPO + "/pulls/" + str(pull_num)
    output_name = "mined_jsons/" + REPO.replace("/", "-") + "-" + str(pull_num) + ".json"

    # Write the output to a file
    with open(output_name, 'w', encoding='utf-8') as f:

        # Make the request
        request = make_request(api_url, GITHUB_USERNAME, GITHUB_AUTH, PULL_PAYLOAD)

        # Convert the request into a JSON file we can parse
        data = request.json()

        # Dump that json to the file
        json.dump(data, f,sort_keys=False)

        # Close the file
        f.close()

    # See if the request was successful
    return request


def make_request(repo, pull_num):
    api_url = REQUEST_URL + repo + "/pulls/" + str(pull_num)

    # Make the request to the api
    r = requests.get(api_url, auth=HTTPBasicAuth( GITHUB_USERNAME, GITHUB_AUTH),
                    proxies=PROXIES, headers=HEADERS, params=PULL_PAYLOAD)
    return r.json()

def run_mining_script():
    # Download the JSON file
    request = download_api_page_json(PULL_NUM)
    return request
    