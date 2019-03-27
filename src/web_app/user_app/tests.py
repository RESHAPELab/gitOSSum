'''
tests.py 

Written by Stephen White 

Created: 3/25/2019

Last Updated: 3/26/2019

A file which contains all relevant test suites that ensure the 
integrity of Git-OSS-Um's backend services. 
'''

from django.test import TestCase
from mining_scripts.send_email import * 
from mining_scripts.mining import *
from mining_scripts import config
from mining_scripts.batchify import *
from .filters import *
from .models import *
from django.utils import timezone
import re


# Setup all variables for testing, ensure mongod is running in the background 
MONGO_CLIENT = MongoClient('localhost', 27017) # Where are we connecting
DB = MONGO_CLIENT.test_db # The specific mongo database we are working with 
REPOS_COLLECTION = DB.repos # collection for storing all of a repo's main api json information 
PULL_REQUESTS_COLLECTION = DB.pullRequests # collection for storing all pull requests for all repos 
PULL_REQUEST_BATCHES_COLLECTION = DB.pullBatches
TEST_REPO = "Swhite9478/OpenSourceDev" # repo for testing purposes 
TEST_REPO_2 = 'google/gumbo-parser'
TEST_REPO_3 = 'Swhite9478/CS386-HoloLens-Project'
TEST_REPO_4 = 'Microsoft/Calculator'
TEST_REPO_5 = 'Samreay/WorkshopExample'
TEST_REPO_6 = 'skeeto/endlessh'
TEST_REPO_7 = 'Swhite9478/Github-Mining-Tool'
GITHUB = Github("Githubfake01", "5RNsya*z#&aA", per_page=100) # authorization for the github API
PYGIT_TEST_REPO = GITHUB.get_repo(TEST_REPO) # Pygit's interpretation of the repo 
PYGIT_TEST_REPO_2 = GITHUB.get_repo(TEST_REPO_2)
PYGIT_TEST_REPO_3 = GITHUB.get_repo(TEST_REPO_3)
PYGIT_TEST_REPO_4 = GITHUB.get_repo(TEST_REPO_4)
PYGIT_TEST_REPO_5 = GITHUB.get_repo(TEST_REPO_5)
PYGIT_TEST_REPO_6 = GITHUB.get_repo(TEST_REPO_6)
PYGIT_TEST_REPO_7 = GITHUB.get_repo(TEST_REPO_7)
TEST_REPO_NUMBER_OF_PULLS = PYGIT_TEST_REPO.get_pulls('all').totalCount
TEST_REPO_2_NUMBER_OF_PULLS = PYGIT_TEST_REPO_2.get_pulls('all').totalCount
TEST_REPO_3_NUMBER_OF_PULLS = PYGIT_TEST_REPO_3.get_pulls('all').totalCount
ZERO, ONE, TWO, THREE = 0, 1, 2, 3

LANGUAGES_LIST = [PYGIT_TEST_REPO_4.language, PYGIT_TEST_REPO_5.language, PYGIT_TEST_REPO_6.language, PYGIT_TEST_REPO_7.language]


mongo_mining_test_init() # Tell the mining script NOT to use the production mongo database
mongo_filter_test_init() # Tell the filter system NOT to use the production mongo database 


# Utility function for testing 
def initialize_batch_json(batch_list, repo_name):
        total_batches = len(batch_list)
        batch_json_data  = {
            "repo": f"{repo_name}",
            "BATCH_SIZE": BATCH_SIZE,
            "total_batches": total_batches,
            "collected_batches": 0,
            "attempted_batches": 0,
            "updated": str(datetime.now())
        }
        DB.pullBatches.update_one(batch_json_data, {"$set": batch_json_data}, upsert=True)


# Test suite for repo landing page 
class RepoLandingPageTestSuite(TestCase):
    # def setUp(self):
    
    def tearDown(self):
        delete_all_repos_from_repo_collection()

    def test_pygit_test_repo_not_none(self):
        self.assertIsNotNone(PYGIT_TEST_REPO)

    def test_pygit_test_repo_2_not_none(self):
        self.assertIsNotNone(PYGIT_TEST_REPO_2)
    
    def test_pygit_test_repo_3_not_none(self):
        self.assertIsNotNone(PYGIT_TEST_REPO_3)

    # Test that we can remove all repos from the repos collection 
    def test_delete_all_from_repos_collection(self):
        delete_all_repos_from_repo_collection()
        number_of_repos = REPOS_COLLECTION.count_documents({})
        self.assertEqual(number_of_repos, ZERO)

    def test_delete_all_from_repos_collection_twice(self):
        delete_all_repos_from_repo_collection()
        delete_all_repos_from_repo_collection()
        number_of_repos = REPOS_COLLECTION.count_documents({})
        self.assertEqual(number_of_repos, ZERO)

    def test_can_mine_one_repo_and_store_in_database(self):
        mine_repo_page(PYGIT_TEST_REPO)
        number_of_repos = REPOS_COLLECTION.count_documents({})
        self.assertEqual(number_of_repos, ONE)

    def test_can_mine_one_repo_and_remove_from_database(self):
        mine_repo_page(PYGIT_TEST_REPO)
        delete_all_repos_from_repo_collection()
        number_of_repos = REPOS_COLLECTION.count_documents({})
        self.assertEqual(number_of_repos, ZERO)

    def test_mining_same_repo_page_twice_doesnt_count_as_two_entries(self):
        mine_repo_page(PYGIT_TEST_REPO)
        mine_repo_page(PYGIT_TEST_REPO)
        number_of_repos = REPOS_COLLECTION.count_documents({})
        self.assertEqual(number_of_repos, ONE)

    def test_mining_same_repo_page_three_times_doesnt_count_as_three_entries(self):
        mine_repo_page(PYGIT_TEST_REPO)
        mine_repo_page(PYGIT_TEST_REPO)
        mine_repo_page(PYGIT_TEST_REPO)
        number_of_repos = REPOS_COLLECTION.count_documents({})
        self.assertEqual(number_of_repos, ONE)

    def test_can_mine_two_repo_pages(self):
       mine_repo_page(PYGIT_TEST_REPO)
       mine_repo_page(PYGIT_TEST_REPO_2)
       number_of_repos = REPOS_COLLECTION.count_documents({})
       self.assertEqual(number_of_repos, TWO)

    def test_mining_two_repo_pages_twice_doesnt_count_as_four_entries(self):
       mine_repo_page(PYGIT_TEST_REPO)
       mine_repo_page(PYGIT_TEST_REPO_2)
       mine_repo_page(PYGIT_TEST_REPO)
       mine_repo_page(PYGIT_TEST_REPO_2)
       number_of_repos = REPOS_COLLECTION.count_documents({})
       self.assertEqual(number_of_repos, TWO)

    def test_can_find_all_repos_1(self):
        delete_all_repos_from_repo_collection()
        mine_repo_page(PYGIT_TEST_REPO)
        repos = get_all_repos()
        count = ZERO
        for repo in repos:
            count += ONE
        self.assertEqual(count, ONE)

    def test_can_find_all_repos_2(self):
        mine_repo_page(PYGIT_TEST_REPO)
        mine_repo_page(PYGIT_TEST_REPO_2)
        repos = get_all_repos()
        count = ZERO
        for repo in repos:
            count += ONE
        self.assertEqual(count, TWO)

    def test_can_find_all_repos_3(self):
        mine_repo_page(PYGIT_TEST_REPO)
        mine_repo_page(PYGIT_TEST_REPO_2)
        mine_repo_page(PYGIT_TEST_REPO_3)
        repos = get_all_repos()
        count = ZERO
        for repo in repos:
            count += ONE
        self.assertEqual(count, THREE)

    def test_can_find_all_repos_4(self):
        mine_repo_page(PYGIT_TEST_REPO)
        mine_repo_page(PYGIT_TEST_REPO_2)
        mine_repo_page(PYGIT_TEST_REPO_3)
        delete_specific_repo_from_repo_collection(TEST_REPO_3)
        repos = get_all_repos()
        count = ZERO
        for repo in repos:
            count += ONE
        self.assertEqual(count, TWO)

    def test_can_find_all_repos_5(self):
        mine_repo_page(PYGIT_TEST_REPO)
        mine_repo_page(PYGIT_TEST_REPO_2)
        mine_repo_page(PYGIT_TEST_REPO_3)
        delete_specific_repo_from_repo_collection(TEST_REPO_3)
        delete_specific_repo_from_repo_collection(TEST_REPO_2)
        repos = get_all_repos()
        count = ZERO
        for repo in repos:
            count += ONE
        self.assertEqual(count, ONE)

    def test_can_find_all_repos_6(self):
        mine_repo_page(PYGIT_TEST_REPO)
        mine_repo_page(PYGIT_TEST_REPO_2)
        mine_repo_page(PYGIT_TEST_REPO_3)
        delete_specific_repo_from_repo_collection(TEST_REPO_3)
        delete_specific_repo_from_repo_collection(TEST_REPO_2)
        delete_specific_repo_from_repo_collection(TEST_REPO)
        repos = get_all_repos()
        count = ZERO
        for repo in repos:
            count += ONE
        self.assertEqual(count, ZERO)

    def test_find_repo_main_page(self):
        mine_repo_page(PYGIT_TEST_REPO)
        test_repo_found = find_repo_main_page(TEST_REPO)
        self.assertEqual(test_repo_found["full_name"], PYGIT_TEST_REPO.full_name)

    def test_find_repo_main_page_created_at_attribute(self):
        mine_repo_page(PYGIT_TEST_REPO)
        test_repo_found = find_repo_main_page(TEST_REPO)
        created_at = tuple(int(num) for num in (re.split('-|T|:|Z', test_repo_found["created_at"]))[:-1])
        pygit_test_repo_created_at = tuple(int(num) for num in (re.split('-| |:', str(PYGIT_TEST_REPO.created_at))))
        self.assertEqual(created_at, pygit_test_repo_created_at)

    def test_find_repo_main_page_owner_login_attribute(self):
        mine_repo_page(PYGIT_TEST_REPO)
        test_repo_found = find_repo_main_page(TEST_REPO)
        self.assertEqual(test_repo_found['owner']['login'], PYGIT_TEST_REPO.owner.login)

    def test_can_find_and_delete_specifc_repo_from_repo_collection(self):
        mine_repo_page(PYGIT_TEST_REPO)
        mine_repo_page(PYGIT_TEST_REPO_2)
        delete_specific_repo_from_repo_collection(TEST_REPO)
        number_of_repos = REPOS_COLLECTION.count_documents({})
        self.assertEqual(number_of_repos, ONE)

    def test_can_find_and_delete_specifc_repo_from_repo_collection_2(self):
        mine_repo_page(PYGIT_TEST_REPO)
        mine_repo_page(PYGIT_TEST_REPO_3)
        delete_specific_repo_from_repo_collection(TEST_REPO)
        test_repo_found = find_repo_main_page(TEST_REPO_3)
        self.assertEqual(test_repo_found['owner']['login'], PYGIT_TEST_REPO_3.owner.login)


# Test suite for pull requests 
class PullRequestTestSuite(TestCase):
    def tearDown(self):
        delete_all_pulls_from_pull_request_collection()
        delete_all_pull_requests_batches_from_batch_collection()

    def test_can_delete_all_from_pull_requests_collection(self):
        delete_all_pulls_from_pull_request_collection()
        number_pull_requests = PULL_REQUESTS_COLLECTION.count_documents({})
        self.assertEqual(number_pull_requests, ZERO)

    def test_can_mine_pull_requests_from_repo(self):
        batch_data = batchify(PYGIT_TEST_REPO.full_name.lower())
        initialize_batch_json(batch_data, PYGIT_TEST_REPO.full_name.lower())
        for batch_job in range(len(batch_data)):
            pulls_batch = get_batch_number(PYGIT_TEST_REPO.full_name.lower(), batch_job)
            mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO.full_name.lower())

        number_pull_requests = PULL_REQUESTS_COLLECTION.count_documents({})
        self.assertEqual(number_pull_requests, TEST_REPO_NUMBER_OF_PULLS)

    def test_mining_pull_requests_twice_from_repo_doesnt_count_as_separate_entries(self):
        batch_data_one = batchify(PYGIT_TEST_REPO.full_name.lower())
        initialize_batch_json(batch_data_one, PYGIT_TEST_REPO.full_name.lower())

        for batch_job in range(len(batch_data_one)):
            pulls_batch = get_batch_number(PYGIT_TEST_REPO.full_name.lower(), batch_job)
            mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO.full_name.lower())
            mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO.full_name.lower())
        
            
        
        number_pull_requests = PULL_REQUESTS_COLLECTION.count_documents({})
        self.assertEqual(number_pull_requests, TEST_REPO_NUMBER_OF_PULLS)

    def test_can_mine_two_separate_repos_pull_requests(self):
        batch_data_one = batchify(PYGIT_TEST_REPO.full_name.lower())
        initialize_batch_json(batch_data_one, PYGIT_TEST_REPO.full_name.lower())

        for batch_job in range(len(batch_data_one)):
            pulls_batch = get_batch_number(PYGIT_TEST_REPO.full_name.lower(), batch_job)
            mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO.full_name.lower())
            mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO.full_name.lower())

        batch_data_two = batchify(PYGIT_TEST_REPO_3.full_name.lower())
        initialize_batch_json(batch_data_two, PYGIT_TEST_REPO_3.full_name.lower())

        for batch_job in range(len(batch_data_one)):
            pulls_batch = get_batch_number(PYGIT_TEST_REPO_3.full_name.lower(), batch_job)
            mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO_3.full_name.lower())
            mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO_3.full_name.lower())

        number_pull_requests = PULL_REQUESTS_COLLECTION.count_documents({})
        total_prs = TEST_REPO_NUMBER_OF_PULLS + TEST_REPO_3_NUMBER_OF_PULLS
        self.assertEqual(number_pull_requests, total_prs)

    def test_can_find_pulls_belonging_to_specific_repo(self):
        batch_data_one = batchify(PYGIT_TEST_REPO.full_name.lower())
        initialize_batch_json(batch_data_one, PYGIT_TEST_REPO.full_name.lower())

        for batch_job in range(len(batch_data_one)):
            pulls_batch = get_batch_number(PYGIT_TEST_REPO.full_name.lower(), batch_job)
            mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO.full_name.lower())
            mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO.full_name.lower())

        batch_data_two = batchify(PYGIT_TEST_REPO_3.full_name.lower())
        initialize_batch_json(batch_data_two, PYGIT_TEST_REPO_3.full_name.lower())

        for batch_job in range(len(batch_data_one)):
            pulls_batch = get_batch_number(PYGIT_TEST_REPO_3.full_name.lower(), batch_job)
            mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO_3.full_name.lower())
            mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO_3.full_name.lower())

        pulls = find_all_pull_requests_from_a_specific_repo(TEST_REPO)
        counter = ZERO
        for pull in pulls:
            counter += ONE
        self.assertEqual(counter, TEST_REPO_NUMBER_OF_PULLS)

    def test_can_find_pulls_belonging_to_specific_repo_2(self):
        batch_data_one = batchify(PYGIT_TEST_REPO.full_name.lower())
        initialize_batch_json(batch_data_one, PYGIT_TEST_REPO.full_name.lower())

        for batch_job in range(len(batch_data_one)):
            pulls_batch = get_batch_number(PYGIT_TEST_REPO.full_name.lower(), batch_job)
            mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO.full_name.lower())
            mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO.full_name.lower())

        batch_data_two = batchify(PYGIT_TEST_REPO_3.full_name.lower())
        initialize_batch_json(batch_data_two, PYGIT_TEST_REPO_3.full_name.lower())

        for batch_job in range(len(batch_data_one)):
            pulls_batch = get_batch_number(PYGIT_TEST_REPO_3.full_name.lower(), batch_job)
            mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO_3.full_name.lower())
            mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO_3.full_name.lower())

        pulls = find_all_pull_requests_from_a_specific_repo(TEST_REPO_3)
        counter = ZERO
        for pull in pulls:
            counter += ONE
        self.assertEqual(counter, TEST_REPO_3_NUMBER_OF_PULLS)

    def test_can_find_all_pulls_1(self):
        batch_data_one = batchify(PYGIT_TEST_REPO.full_name.lower())
        initialize_batch_json(batch_data_one, PYGIT_TEST_REPO.full_name.lower())

        for batch_job in range(len(batch_data_one)):
            pulls_batch = get_batch_number(PYGIT_TEST_REPO.full_name.lower(), batch_job)
            mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO.full_name.lower())
            mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO.full_name.lower())

        pulls = get_all_pull_requests()
        counter = ZERO
        for pull in pulls:
            counter += ONE
        self.assertEqual(counter, TEST_REPO_NUMBER_OF_PULLS)

    def test_can_find_all_pulls_2(self):
        batch_data_one = batchify(PYGIT_TEST_REPO_2.full_name.lower())
        initialize_batch_json(batch_data_one, PYGIT_TEST_REPO_2.full_name.lower())

        for batch_job in range(len(batch_data_one)):
            pulls_batch = get_batch_number(PYGIT_TEST_REPO_2.full_name.lower(), batch_job)
            mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO_2.full_name.lower())
            mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO_2.full_name.lower())

        pulls = get_all_pull_requests()
        counter = ZERO
        for pull in pulls:
            counter += ONE
        self.assertEqual(counter, TEST_REPO_2_NUMBER_OF_PULLS)

    def test_can_find_all_pulls_3(self):
        batch_data_one = batchify(PYGIT_TEST_REPO.full_name.lower())
        initialize_batch_json(batch_data_one, PYGIT_TEST_REPO.full_name.lower())

        for batch_job in range(len(batch_data_one)):
            pulls_batch = get_batch_number(PYGIT_TEST_REPO.full_name.lower(), batch_job)
            mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO.full_name.lower())
            mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO.full_name.lower())

        batch_data_two = batchify(PYGIT_TEST_REPO_2.full_name.lower())
        initialize_batch_json(batch_data_two, PYGIT_TEST_REPO_2.full_name.lower())

        for batch_job in range(len(batch_data_one)):
            pulls_batch = get_batch_number(PYGIT_TEST_REPO_2.full_name.lower(), batch_job)
            mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO_2.full_name.lower())
            mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO_2.full_name.lower())

        pulls = get_all_pull_requests()
        counter = ZERO
        for pull in pulls:
            counter += ONE
        real_number_of_pulls = TEST_REPO_NUMBER_OF_PULLS + TEST_REPO_2_NUMBER_OF_PULLS
        self.assertEqual(counter, real_number_of_pulls)


    def test_can_find_and_delete_specifc_repos_pull_requests_1(self):
        batch_data_one = batchify(PYGIT_TEST_REPO.full_name.lower())
        initialize_batch_json(batch_data_one, PYGIT_TEST_REPO.full_name.lower())

        for batch_job in range(len(batch_data_one)):
            pulls_batch = get_batch_number(PYGIT_TEST_REPO.full_name.lower(), batch_job)
            mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO.full_name.lower())
            mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO.full_name.lower())

        batch_data_two = batchify(PYGIT_TEST_REPO_3.full_name.lower())
        initialize_batch_json(batch_data_two, PYGIT_TEST_REPO_3.full_name.lower())

        for batch_job in range(len(batch_data_one)):
            pulls_batch = get_batch_number(PYGIT_TEST_REPO_3.full_name.lower(), batch_job)
            mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO_3.full_name.lower())
            mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO_3.full_name.lower())

        delete_specifc_repos_pull_requests(TEST_REPO_3)
        pulls = get_all_pull_requests()
        counter = ZERO
        for pull in pulls:
            counter += ONE
        real_number_of_pulls = TEST_REPO_NUMBER_OF_PULLS
        self.assertEqual(counter, real_number_of_pulls)

    def test_can_find_and_delete_specifc_repos_pull_requests_2(self):
        batch_data_one = batchify(PYGIT_TEST_REPO.full_name.lower())
        initialize_batch_json(batch_data_one, PYGIT_TEST_REPO.full_name.lower())

        for batch_job in range(len(batch_data_one)):
            pulls_batch = get_batch_number(PYGIT_TEST_REPO.full_name.lower(), batch_job)
            mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO.full_name.lower())
            mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO.full_name.lower())

        batch_data_two = batchify(PYGIT_TEST_REPO_3.full_name.lower())
        initialize_batch_json(batch_data_two, PYGIT_TEST_REPO_3.full_name.lower())

        for batch_job in range(len(batch_data_one)):
            pulls_batch = get_batch_number(PYGIT_TEST_REPO_3.full_name.lower(), batch_job)
            mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO_3.full_name.lower())
            mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO_3.full_name.lower())

        delete_specifc_repos_pull_requests(TEST_REPO)
        pulls = get_all_pull_requests()
        counter = ZERO
        for pull in pulls:
            counter += ONE
        self.assertEqual(counter, TEST_REPO_3_NUMBER_OF_PULLS)

    def test_can_find_and_delete_specifc_repos_pull_requests_3(self):
        batch_data_one = batchify(PYGIT_TEST_REPO.full_name.lower())
        initialize_batch_json(batch_data_one, PYGIT_TEST_REPO.full_name.lower())

        for batch_job in range(len(batch_data_one)):
            pulls_batch = get_batch_number(PYGIT_TEST_REPO.full_name.lower(), batch_job)
            mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO.full_name.lower())
            mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO.full_name.lower())

        batch_data_two = batchify(PYGIT_TEST_REPO_3.full_name.lower())
        initialize_batch_json(batch_data_two, PYGIT_TEST_REPO_3.full_name.lower())

        for batch_job in range(len(batch_data_one)):
            pulls_batch = get_batch_number(PYGIT_TEST_REPO_3.full_name.lower(), batch_job)
            mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO_3.full_name.lower())
            mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO_3.full_name.lower())

        delete_specifc_repos_pull_requests(TEST_REPO)
        delete_specifc_repos_pull_requests(TEST_REPO_3)
        pulls = get_all_pull_requests()
        counter = ZERO
        for pull in pulls:
            counter += ONE
        self.assertEqual(counter, ZERO)


# Test suite for the combination of landing page and pull requests 
class ExtraMiningTestSuite(TestCase):

    def tearDown(self):
        delete_all_repos_from_repo_collection()
        delete_all_pulls_from_pull_request_collection()
        delete_all_pull_requests_batches_from_batch_collection()
    
    def test_can_delete_all_repos_and_pulls_in_one_call(self):
        batch_data_one = batchify(PYGIT_TEST_REPO.full_name.lower())
        initialize_batch_json(batch_data_one, PYGIT_TEST_REPO.full_name.lower())

        for batch_job in range(len(batch_data_one)):
            pulls_batch = get_batch_number(PYGIT_TEST_REPO.full_name.lower(), batch_job)
            mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO.full_name.lower())
            mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO.full_name.lower())

        batch_data_two = batchify(PYGIT_TEST_REPO_3.full_name.lower())
        initialize_batch_json(batch_data_two, PYGIT_TEST_REPO_3.full_name.lower())

        for batch_job in range(len(batch_data_one)):
            pulls_batch = get_batch_number(PYGIT_TEST_REPO_3.full_name.lower(), batch_job)
            mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO_3.full_name.lower())
            mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO_3.full_name.lower())

        delete_all_contents_from_every_collection()

        number_of_repos = REPOS_COLLECTION.count_documents({})
        number_of_pulls = PULL_REQUESTS_COLLECTION.count_documents({})
        number_of_batches = PULL_REQUEST_BATCHES_COLLECTION.count_documents({})

        self.assertEqual(number_of_repos, ZERO)
        self.assertEqual(number_of_pulls, ZERO)
        self.assertEqual(number_of_batches, ZERO)

    def test_can_delete_all_repos_and_pulls_for_specific_repo_in_one_call(self):
        mine_repo_page(PYGIT_TEST_REPO)
        mine_repo_page(PYGIT_TEST_REPO_3)

        batch_data_one = batchify(PYGIT_TEST_REPO.full_name.lower())
        initialize_batch_json(batch_data_one, PYGIT_TEST_REPO.full_name.lower())

        for batch_job in range(len(batch_data_one)):
            pulls_batch = get_batch_number(PYGIT_TEST_REPO.full_name.lower(), batch_job)
            mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO.full_name.lower())
            mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO.full_name.lower())

        batch_data_two = batchify(PYGIT_TEST_REPO_3.full_name.lower())
        initialize_batch_json(batch_data_two, PYGIT_TEST_REPO_3.full_name.lower())

        for batch_job in range(len(batch_data_one)):
            pulls_batch = get_batch_number(PYGIT_TEST_REPO_3.full_name.lower(), batch_job)
            mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO_3.full_name.lower())
            mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO_3.full_name.lower())

        delete_all_contents_of_specific_repo_from_every_collection(TEST_REPO_3)
        number_of_repos = REPOS_COLLECTION.count_documents({})
        number_of_pulls = PULL_REQUESTS_COLLECTION.count_documents({})
        self.assertEqual(number_of_repos, ONE)
        self.assertEqual(find_repo_main_page(TEST_REPO)["full_name"], PYGIT_TEST_REPO.full_name)
        self.assertEqual(find_all_pull_requests_from_a_specific_repo(TEST_REPO)[0]["user"]["login"], "Swhite9478")
        self.assertEqual(find_all_pull_requests_from_a_specific_repo(TEST_REPO)[0]["head"]["repo"]["full_name"], TEST_REPO)
        self.assertEqual(number_of_pulls, TEST_REPO_NUMBER_OF_PULLS)


# Test suite for sending emails 
class EmailTestSuite(TestCase): 
    def test_can_send_mining_initialized_email(self):
        success = send_mining_initialized_email("UNIT TEST REPO", "ADMINISTRATOR", config.EMAIL_ADDRESS)
        self.assertTrue(success)

    def test_can_send_mining_completed_email(self):
        success = send_confirmation_email("UNIT TEST REPO", "ADMINISTRATOR", config.EMAIL_ADDRESS)
        self.assertTrue(success)

    def test_can_send_mining_denied_email(self):
        success = send_repository_denied_email("UNIT TEST REPO", "ADMINISTRATOR", config.EMAIL_ADDRESS)
        self.assertTrue(success)

    def test_can_send_mining_blacklisted_email(self):
        success = send_repository_blacklist_email("UNIT TEST REPO", "ADMINISTRATOR", config.EMAIL_ADDRESS)
        self.assertTrue(success)

class RepoNameTestSuite(TestCase):
    valid_repo = re.compile('^(((\w+)[-]*)\w+)+/+((\w+)([-]|[.])*)+\w+$')

    def test_invalid_repo_name_1(self):
        repo_name = 'john'
        self.assertFalse(self.valid_repo.fullmatch(repo_name))
    
    def test_invalid_repo_name_2(self):
        repo_name = '/john/repo'
        self.assertFalse(self.valid_repo.fullmatch(repo_name))

    def test_invalid_repo_name_3(self):
        repo_name = '.john/repo'
        self.assertFalse(self.valid_repo.fullmatch(repo_name))

    def test_invalid_repo_name_4(self):
        repo_name = '$john/repo'
        self.assertFalse(self.valid_repo.fullmatch(repo_name))

    def test_invalid_repo_name_5(self):
        repo_name = '~john/repo'
        self.assertFalse(self.valid_repo.fullmatch(repo_name))

    def test_invalid_repo_name_6(self):
        repo_name = 'john-/repo'
        self.assertFalse(self.valid_repo.fullmatch(repo_name))

    def test_invalid_repo_name_7(self):
        repo_name = 'john/-repo'
        self.assertFalse(self.valid_repo.fullmatch(repo_name))
    
    def test_invalid_repo_name_8(self):
        repo_name = 'john/.repo'
        self.assertFalse(self.valid_repo.fullmatch(repo_name))

    def test_invalid_repo_name_9(self):
        repo_name = 'john/$repo'
        self.assertFalse(self.valid_repo.fullmatch(repo_name))

    def test_invalid_repo_name_10(self):
        repo_name = 'john/~repo'
        self.assertFalse(self.valid_repo.fullmatch(repo_name))

    def test_invalid_repo_name_11(self):
        repo_name = 'jo[hn]/repo'
        self.assertFalse(self.valid_repo.fullmatch(repo_name))

    def test_invalid_repo_name_12(self):
        repo_name = 'john/r[epo'
        self.assertFalse(self.valid_repo.fullmatch(repo_name))

    def test_invalid_repo_name_13(self):
        repo_name = 'jo{hn/re}po'
        self.assertFalse(self.valid_repo.fullmatch(repo_name))

    def test_invalid_repo_name_14(self):
        repo_name = 'jo+hn/repo'
        self.assertFalse(self.valid_repo.fullmatch(repo_name))

    def test_valid_repo_name_1(self):
        repo_name = 'Swhite9478/OpenSourceDev'
        self.assertTrue(self.valid_repo.fullmatch(repo_name))

    def test_valid_repo_name_2(self):
        repo_name = 'repo/repo.js'
        self.assertTrue(self.valid_repo.fullmatch(repo_name))

    def test_valid_repo_name_3(self):
        repo_name = 'repo/another-valid-repo.swag'
        self.assertTrue(self.valid_repo.fullmatch(repo_name))

    def test_repo_exists_1(self):
        repo_name = 'google/gumbo-parser'
        self.assertNotIsInstance(find_repo_main_page(repo_name), Exception)

    def test_repo_exists_2(self):
        repo_name = 'jabref/jabref'
        self.assertNotIsInstance(find_repo_main_page(repo_name), Exception)

    def test_repo_exists_3(self):
        repo_name = 'rails/rails'
        self.assertNotIsInstance(find_repo_main_page(repo_name), Exception)

    def test_repo_exists_4(self):
        repo_name = 'swhite9478/opensourcedev'
        self.assertNotIsInstance(find_repo_main_page(repo_name), Exception)

    def test_repo_exists_5(self):
        repo_name = 'torvalds/linux'
        self.assertNotIsInstance(find_repo_main_page(repo_name), Exception)

    def test_repo_does_not_exist_1(self):
        repo_name = 'fake/repo'
        self.assertIsInstance(find_repo_main_page(repo_name), Exception)

    def test_repo_does_not_exist_2(self):
        repo_name = 'thisis/not-a-real.repo'
        self.assertIsInstance(find_repo_main_page(repo_name), Exception)

    def test_repo_does_not_exist_3(self):
        repo_name = '1234I-cant-believe/you-tried_to.fool-me'
        self.assertIsInstance(find_repo_main_page(repo_name), Exception)

    def test_repo_does_not_exist_4(self):
        repo_name = 'here.we/go-again'
        self.assertIsInstance(find_repo_main_page(repo_name), Exception)

    def test_repo_does_not_exist_5(self):
        repo_name = '1234/5678'
        self.assertIsInstance(find_repo_main_page(repo_name), Exception)

# Setup class to initialize filter test suite 
class Singleton(object):
    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:

            # Create the instance of this class
            cls._instance = super(Singleton, cls).__new__(
                            cls, *args, **kwargs)

            # The following code will only be executed once:

            # Mine all of the landing pages we want to test 
            mine_repo_page(PYGIT_TEST_REPO_4)
            mine_repo_page(PYGIT_TEST_REPO_5)
            mine_repo_page(PYGIT_TEST_REPO_6)
            mine_repo_page(PYGIT_TEST_REPO_7)

            # Batch and initialize each repo for pull collection 
            batch_data_one = batchify(PYGIT_TEST_REPO_4.full_name.lower())
            batch_data_two = batchify(PYGIT_TEST_REPO_5.full_name.lower())
            batch_data_three = batchify(PYGIT_TEST_REPO_6.full_name.lower())
            batch_data_four = batchify(PYGIT_TEST_REPO_7.full_name.lower())

            initialize_batch_json(batch_data_one, PYGIT_TEST_REPO_4.full_name.lower())
            initialize_batch_json(batch_data_two, PYGIT_TEST_REPO_5.full_name.lower())
            initialize_batch_json(batch_data_three, PYGIT_TEST_REPO_6.full_name.lower())
            initialize_batch_json(batch_data_four, PYGIT_TEST_REPO_7.full_name.lower())

            # Mine the pull requests for each test repo 
            for batch_job in range(len(batch_data_one)):
                pulls_batch = get_batch_number(PYGIT_TEST_REPO_4.full_name.lower(), batch_job)
                mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO_4.full_name.lower())
                mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO_4.full_name.lower())

            for batch_job in range(len(batch_data_two)):
                pulls_batch = get_batch_number(PYGIT_TEST_REPO_5.full_name.lower(), batch_job)
                mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO_5.full_name.lower())
                mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO_5.full_name.lower())

            for batch_job in range(len(batch_data_three)):
                pulls_batch = get_batch_number(PYGIT_TEST_REPO_6.full_name.lower(), batch_job)
                mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO_6.full_name.lower())
                mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO_6.full_name.lower())

            for batch_job in range(len(batch_data_four)):
                pulls_batch = get_batch_number(PYGIT_TEST_REPO_7.full_name.lower(), batch_job)
                mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO_7.full_name.lower())
                mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO_7.full_name.lower())

            # Set the setUpBool flag for this class to true so we dont go 
            # setting all of this up again 
            cls.setUpBool = True

        return cls._instance

class FilterTestSuite(TestCase):
    def setUp(self):
        # The first call initializes singleton, every additional call
        # returns the instantiated reference.
        if REPOS_COLLECTION.count_documents({}) == 0:
            print(Singleton().setUpBool)

    # Make sure that the language list is correct 
    def test_can_get_language_list(self):
        obtained_languages_list = get_language_list_from_mongo()
        for language in obtained_languages_list:
            self.assertTrue(language in LANGUAGES_LIST)

    def test_can_filter_by_language_1(self):
        language = PYGIT_TEST_REPO_4.language
        obtained_repos_by_language = get_repos_list_by_language_filter([language])
        self.assertTrue(PYGIT_TEST_REPO_4.full_name.lower() in obtained_repos_by_language)

    def test_can_filter_by_language_2(self):
        language = PYGIT_TEST_REPO_5.language
        obtained_repos_by_language = get_repos_list_by_language_filter([language])
        self.assertTrue(PYGIT_TEST_REPO_5.full_name.lower() in obtained_repos_by_language)

    def test_can_filter_by_language_3(self):
        language = PYGIT_TEST_REPO_6.language
        obtained_repos_by_language = get_repos_list_by_language_filter([language])
        self.assertTrue(PYGIT_TEST_REPO_6.full_name.lower() in obtained_repos_by_language)

    def test_can_filter_by_language_4(self):
        language = PYGIT_TEST_REPO_7.language
        obtained_repos_by_language = get_repos_list_by_language_filter([language])
        self.assertTrue(PYGIT_TEST_REPO_7.full_name.lower() in obtained_repos_by_language)

    def test_can_filter_by_pulls_less_than_1(self):
        num_pulls = len([item for batch in batchify(PYGIT_TEST_REPO_4.full_name) for item in batch]) 
        filtered_repos = get_repos_list_by_pulls_less_than_filter(num_pulls + 1)
        self.assertTrue(PYGIT_TEST_REPO_4.full_name.lower() in filtered_repos)

    def test_can_filter_by_pulls_less_than_2(self):
        num_pulls = len([item for batch in batchify(PYGIT_TEST_REPO_5.full_name) for item in batch]) 
        filtered_repos = get_repos_list_by_pulls_less_than_filter(num_pulls + 1)
        self.assertTrue(PYGIT_TEST_REPO_5.full_name.lower() in filtered_repos)

    def test_can_filter_by_pulls_less_than_3(self):
        num_pulls = len([item for batch in batchify(PYGIT_TEST_REPO_6.full_name) for item in batch]) 
        filtered_repos = get_repos_list_by_pulls_less_than_filter(num_pulls + 1)
        self.assertTrue(PYGIT_TEST_REPO_6.full_name.lower() in filtered_repos)

    def test_can_filter_by_pulls_less_than_4(self):
        num_pulls = len([item for batch in batchify(PYGIT_TEST_REPO_7.full_name) for item in batch]) 
        filtered_repos = get_repos_list_by_pulls_less_than_filter(num_pulls + 1)
        self.assertTrue(PYGIT_TEST_REPO_7.full_name.lower() in filtered_repos)
        
    def test_can_filter_by_pulls_greater_than_1(self):
        num_pulls = len([item for batch in batchify(PYGIT_TEST_REPO_4.full_name) for item in batch]) - 1 
        filtered_repos = get_repos_list_by_pulls_greater_than_filter(num_pulls - 1)
        self.assertTrue(PYGIT_TEST_REPO_4.full_name.lower() in filtered_repos)

    def test_can_filter_by_pulls_greater_than_2(self):
        num_pulls = len([item for batch in batchify(PYGIT_TEST_REPO_5.full_name) for item in batch]) - 1
        filtered_repos = get_repos_list_by_pulls_greater_than_filter(num_pulls - 1)
        self.assertTrue(PYGIT_TEST_REPO_5.full_name.lower() in filtered_repos)

    def test_can_filter_by_pulls_greater_than_3(self):
        num_pulls = len([item for batch in batchify(PYGIT_TEST_REPO_6.full_name) for item in batch]) - 1
        filtered_repos = get_repos_list_by_pulls_greater_than_filter(num_pulls - 1)
        self.assertTrue(PYGIT_TEST_REPO_6.full_name.lower() in filtered_repos)

    def test_can_filter_by_pulls_greater_than_4(self):
        num_pulls = len([item for batch in batchify(PYGIT_TEST_REPO_7.full_name) for item in batch]) - 1
        filtered_repos = get_repos_list_by_pulls_greater_than_filter(num_pulls - 1)
        self.assertTrue(PYGIT_TEST_REPO_7.full_name.lower() in filtered_repos)

    def test_can_filter_by_pulls_bounded_1(self):
        lower_bound = 0
        upper_bound = 1000
        filtered_repos = get_repos_list_by_pulls_bounded_filter(lower_bound, upper_bound)
        self.assertTrue(len(filtered_repos) == 4)

    def test_can_filter_by_pulls_bounded_2(self):
        lower_bound = 0
        upper_bound = 1
        filtered_repos = get_repos_list_by_pulls_bounded_filter(lower_bound, upper_bound)
        self.assertTrue(len(filtered_repos) == 0)

    def test_can_filter_by_pulls_bounded_3(self):
        lower_bound = 100
        upper_bound = 100000
        filtered_repos = get_repos_list_by_pulls_bounded_filter(lower_bound, upper_bound)
        self.assertTrue(len(filtered_repos) == 1)
        self.assertTrue(PYGIT_TEST_REPO_4.full_name.lower() in filtered_repos)

    def test_can_filter_by_pulls_bounded_4(self):
        lower_bound = 0
        upper_bound = 10
        filtered_repos = get_repos_list_by_pulls_bounded_filter(lower_bound, upper_bound)
        self.assertTrue(PYGIT_TEST_REPO_7.full_name.lower() in filtered_repos)

    def test_can_filter_by_has_wiki_1(self):
        filtered_repos = get_repos_list_has_wiki_filter(True)
        self.assertTrue(PYGIT_TEST_REPO_4.full_name.lower() not in filtered_repos)

    def test_can_filter_by_has_wiki_2(self):
        filtered_repos = get_repos_list_has_wiki_filter(True)
        self.assertTrue(PYGIT_TEST_REPO_7.full_name.lower() in filtered_repos)

    def test_can_filter_by_search_1(self):
        filtered_repos = get_repos_search_query_filter(PYGIT_TEST_REPO_4.full_name.lower()[0:5])
        self.assertTrue(PYGIT_TEST_REPO_4.full_name.lower() in filtered_repos)

    def test_can_filter_by_search_2(self):
        filtered_repos = get_repos_search_query_filter(PYGIT_TEST_REPO_5.full_name.lower()[0:5])
        self.assertTrue(PYGIT_TEST_REPO_5.full_name.lower() in filtered_repos)

    def test_can_filter_by_search_3(self):
        filtered_repos = get_repos_search_query_filter(PYGIT_TEST_REPO_6.full_name.lower()[0:5])
        self.assertTrue(PYGIT_TEST_REPO_6.full_name.lower() in filtered_repos)

    def test_can_filter_by_search_4(self):
        filtered_repos = get_repos_search_query_filter(PYGIT_TEST_REPO_7.full_name.lower()[0:5])
        self.assertTrue(PYGIT_TEST_REPO_7.full_name.lower() in filtered_repos)

    def test_can_filter_by_search_5(self):
        filtered_repos = get_repos_search_query_filter("ThisShould/Return-Nothing")
        self.assertTrue(len(filtered_repos) == 0)

    def test_can_filter_using_multiple_criteria_1(self):
        lower_bound = 100
        upper_bound = 1000
        filtered_repos_bounded = get_repos_list_by_pulls_bounded_filter(lower_bound, upper_bound)
        filtered_repos_search = get_repos_search_query_filter(PYGIT_TEST_REPO_4.full_name.lower()[0:5])
        filtered_repos_wiki = get_repos_list_has_wiki_filter(False)
        filtered_repos_combined = get_filtered_repos_list([filtered_repos_bounded,
                                                           filtered_repos_search, 
                                                           filtered_repos_wiki]
                                                         )
        self.assertTrue(len(filtered_repos_combined) == 1)
        self.assertTrue(PYGIT_TEST_REPO_4.full_name.lower() in filtered_repos_combined)

    def test_can_filter_using_multiple_criteria_2(self):
        lower_bound = 0
        upper_bound = 1000
        filtered_repos_bounded = get_repos_list_by_pulls_bounded_filter(lower_bound, upper_bound)
        filtered_repos_search = get_repos_search_query_filter(PYGIT_TEST_REPO_2.full_name.lower()[0:5])
        filtered_repos_wiki = get_repos_list_has_wiki_filter(True)
        filtered_repos_combined = get_filtered_repos_list([filtered_repos_bounded,
                                                           filtered_repos_search, 
                                                           filtered_repos_wiki]
                                                         )
        self.assertTrue(len(filtered_repos_combined) == 0)

    def test_can_filter_using_multiple_criteria_3(self):
        lower_bound = 0
        upper_bound = 1000
        filtered_repos_bounded = get_repos_list_by_pulls_bounded_filter(lower_bound, upper_bound)
        filtered_repos_search = get_repos_search_query_filter(PYGIT_TEST_REPO_7.full_name.lower()[0:5])
        filtered_repos_wiki = get_repos_list_has_wiki_filter(True)
        filtered_repos_combined = get_filtered_repos_list([filtered_repos_bounded,
                                                           filtered_repos_search, 
                                                           filtered_repos_wiki]
                                                         )
        self.assertTrue(len(filtered_repos_combined) == 1)
        self.assertTrue(PYGIT_TEST_REPO_7.full_name.lower() in filtered_repos_combined)

class ModelTestSuite(TestCase):

    def tearDown(self):
        MinedRepo.objects.all().delete()

    def test_visualization_extraction_1(self):
        visualization_data = extract_pull_request_model_data(PYGIT_TEST_REPO_4)
        mined_repo = MinedRepo(
            repo_name=PYGIT_TEST_REPO_4.full_name.lower(),
            requested_by="Admin",
            num_pulls=visualization_data["num_pulls"],
            num_closed_merged_pulls=visualization_data["num_closed_merged_pulls"],
            num_closed_unmerged_pulls=visualization_data["num_closed_unmerged_pulls"],
            num_open_pulls=visualization_data["num_open_pulls"],
            created_at_list=visualization_data["created_at_list"],
            closed_at_list=visualization_data["closed_at_list"],
            merged_at_list=visualization_data["merged_at_list"],
            num_newcomer_labels=visualization_data["num_newcomer_labels"],
            bar_chart_html=visualization_data["bar_chart"],
            pull_line_chart_html=visualization_data["line_chart"],
            accepted_timestamp=timezone.now(),
            requested_timestamp=timezone.now()
        ) 

        mined_repo.save()
        
        sql_obj = MinedRepo.objects.get(repo_name=PYGIT_TEST_REPO_4.full_name.lower())
        self.assertEqual(getattr(sql_obj, "repo_name"), PYGIT_TEST_REPO_4.full_name.lower())
        self.assertEqual(getattr(sql_obj, "requested_by"), "Admin")
        self.assertEqual(getattr(sql_obj, "num_pulls"), visualization_data['num_pulls'])
        self.assertEqual(getattr(sql_obj, "num_closed_merged_pulls"), visualization_data['num_closed_merged_pulls'])
        self.assertEqual(getattr(sql_obj, "num_closed_unmerged_pulls"), visualization_data['num_closed_unmerged_pulls'])
        self.assertEqual(getattr(sql_obj, "num_open_pulls"), visualization_data['num_open_pulls'])
        self.assertEqual(getattr(sql_obj, "created_at_list"), visualization_data['created_at_list'])
        self.assertEqual(getattr(sql_obj, "closed_at_list"), visualization_data['closed_at_list'])
        self.assertEqual(getattr(sql_obj, "merged_at_list"), visualization_data['merged_at_list'])
        self.assertEqual(getattr(sql_obj, "num_newcomer_labels"), visualization_data['num_newcomer_labels'])
        self.assertEqual(getattr(sql_obj, "bar_chart_html"), visualization_data['bar_chart'])
        self.assertEqual(getattr(sql_obj, "pull_line_chart_html"), visualization_data['line_chart'])

    def test_visualization_extraction_2(self):
        visualization_data = extract_pull_request_model_data(PYGIT_TEST_REPO_5)
        mined_repo = MinedRepo(
            repo_name=PYGIT_TEST_REPO_5.full_name.lower(),
            requested_by="Admin",
            num_pulls=visualization_data["num_pulls"],
            num_closed_merged_pulls=visualization_data["num_closed_merged_pulls"],
            num_closed_unmerged_pulls=visualization_data["num_closed_unmerged_pulls"],
            num_open_pulls=visualization_data["num_open_pulls"],
            created_at_list=visualization_data["created_at_list"],
            closed_at_list=visualization_data["closed_at_list"],
            merged_at_list=visualization_data["merged_at_list"],
            num_newcomer_labels=visualization_data["num_newcomer_labels"],
            bar_chart_html=visualization_data["bar_chart"],
            pull_line_chart_html=visualization_data["line_chart"],
            accepted_timestamp=timezone.now(),
            requested_timestamp=timezone.now()
        ) 

        mined_repo.save()
        
        sql_obj = MinedRepo.objects.get(repo_name=PYGIT_TEST_REPO_5.full_name.lower())
        self.assertEqual(getattr(sql_obj, "repo_name"), PYGIT_TEST_REPO_5.full_name.lower())
        self.assertEqual(getattr(sql_obj, "requested_by"), "Admin")
        self.assertEqual(getattr(sql_obj, "num_pulls"), visualization_data['num_pulls'])
        self.assertEqual(getattr(sql_obj, "num_closed_merged_pulls"), visualization_data['num_closed_merged_pulls'])
        self.assertEqual(getattr(sql_obj, "num_closed_unmerged_pulls"), visualization_data['num_closed_unmerged_pulls'])
        self.assertEqual(getattr(sql_obj, "num_open_pulls"), visualization_data['num_open_pulls'])
        self.assertEqual(getattr(sql_obj, "created_at_list"), visualization_data['created_at_list'])
        self.assertEqual(getattr(sql_obj, "closed_at_list"), visualization_data['closed_at_list'])
        self.assertEqual(getattr(sql_obj, "merged_at_list"), visualization_data['merged_at_list'])
        self.assertEqual(getattr(sql_obj, "num_newcomer_labels"), visualization_data['num_newcomer_labels'])
        self.assertEqual(getattr(sql_obj, "bar_chart_html"), visualization_data['bar_chart'])
        self.assertEqual(getattr(sql_obj, "pull_line_chart_html"), visualization_data['line_chart'])

    def test_visualization_extraction_3(self):
        visualization_data = extract_pull_request_model_data(PYGIT_TEST_REPO_6)
        mined_repo = MinedRepo(
            repo_name=PYGIT_TEST_REPO_6.full_name.lower(),
            requested_by="Admin",
            num_pulls=visualization_data["num_pulls"],
            num_closed_merged_pulls=visualization_data["num_closed_merged_pulls"],
            num_closed_unmerged_pulls=visualization_data["num_closed_unmerged_pulls"],
            num_open_pulls=visualization_data["num_open_pulls"],
            created_at_list=visualization_data["created_at_list"],
            closed_at_list=visualization_data["closed_at_list"],
            merged_at_list=visualization_data["merged_at_list"],
            num_newcomer_labels=visualization_data["num_newcomer_labels"],
            bar_chart_html=visualization_data["bar_chart"],
            pull_line_chart_html=visualization_data["line_chart"],
            accepted_timestamp=timezone.now(),
            requested_timestamp=timezone.now()
        ) 

        mined_repo.save()
        
        sql_obj = MinedRepo.objects.get(repo_name=PYGIT_TEST_REPO_6.full_name.lower())
        self.assertEqual(getattr(sql_obj, "repo_name"), PYGIT_TEST_REPO_6.full_name.lower())
        self.assertEqual(getattr(sql_obj, "requested_by"), "Admin")
        self.assertEqual(getattr(sql_obj, "num_pulls"), visualization_data['num_pulls'])
        self.assertEqual(getattr(sql_obj, "num_closed_merged_pulls"), visualization_data['num_closed_merged_pulls'])
        self.assertEqual(getattr(sql_obj, "num_closed_unmerged_pulls"), visualization_data['num_closed_unmerged_pulls'])
        self.assertEqual(getattr(sql_obj, "num_open_pulls"), visualization_data['num_open_pulls'])
        self.assertEqual(getattr(sql_obj, "created_at_list"), visualization_data['created_at_list'])
        self.assertEqual(getattr(sql_obj, "closed_at_list"), visualization_data['closed_at_list'])
        self.assertEqual(getattr(sql_obj, "merged_at_list"), visualization_data['merged_at_list'])
        self.assertEqual(getattr(sql_obj, "num_newcomer_labels"), visualization_data['num_newcomer_labels'])
        self.assertEqual(getattr(sql_obj, "bar_chart_html"), visualization_data['bar_chart'])
        self.assertEqual(getattr(sql_obj, "pull_line_chart_html"), visualization_data['line_chart'])

    def test_visualization_extraction_4(self):
        visualization_data = extract_pull_request_model_data(PYGIT_TEST_REPO_7)
        mined_repo = MinedRepo(
            repo_name=PYGIT_TEST_REPO_7.full_name.lower(),
            requested_by="Admin",
            num_pulls=visualization_data["num_pulls"],
            num_closed_merged_pulls=visualization_data["num_closed_merged_pulls"],
            num_closed_unmerged_pulls=visualization_data["num_closed_unmerged_pulls"],
            num_open_pulls=visualization_data["num_open_pulls"],
            created_at_list=visualization_data["created_at_list"],
            closed_at_list=visualization_data["closed_at_list"],
            merged_at_list=visualization_data["merged_at_list"],
            num_newcomer_labels=visualization_data["num_newcomer_labels"],
            bar_chart_html=visualization_data["bar_chart"],
            pull_line_chart_html=visualization_data["line_chart"],
            accepted_timestamp=timezone.now(),
            requested_timestamp=timezone.now()
        ) 

        mined_repo.save()
        
        sql_obj = MinedRepo.objects.get(repo_name=PYGIT_TEST_REPO_7.full_name.lower())
        self.assertEqual(getattr(sql_obj, "repo_name"), PYGIT_TEST_REPO_7.full_name.lower())
        self.assertEqual(getattr(sql_obj, "requested_by"), "Admin")
        self.assertEqual(getattr(sql_obj, "num_pulls"), visualization_data['num_pulls'])
        self.assertEqual(getattr(sql_obj, "num_closed_merged_pulls"), visualization_data['num_closed_merged_pulls'])
        self.assertEqual(getattr(sql_obj, "num_closed_unmerged_pulls"), visualization_data['num_closed_unmerged_pulls'])
        self.assertEqual(getattr(sql_obj, "num_open_pulls"), visualization_data['num_open_pulls'])
        self.assertEqual(getattr(sql_obj, "created_at_list"), visualization_data['created_at_list'])
        self.assertEqual(getattr(sql_obj, "closed_at_list"), visualization_data['closed_at_list'])
        self.assertEqual(getattr(sql_obj, "merged_at_list"), visualization_data['merged_at_list'])
        self.assertEqual(getattr(sql_obj, "num_newcomer_labels"), visualization_data['num_newcomer_labels'])
        self.assertEqual(getattr(sql_obj, "bar_chart_html"), visualization_data['bar_chart'])
        self.assertEqual(getattr(sql_obj, "pull_line_chart_html"), visualization_data['line_chart'])
