from django.test import TestCase
from mining_scripts.send_email import * 
from mining_scripts.mining import *
from mining_scripts import config
from mining_scripts.batchify import *
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
GITHUB = Github("Githubfake01", "5RNsya*z#&aA", per_page=100) # authorization for the github API
PYGIT_TEST_REPO = GITHUB.get_repo(TEST_REPO) # Pygit's interpretation of the repo 
PYGIT_TEST_REPO_2 = GITHUB.get_repo(TEST_REPO_2)
PYGIT_TEST_REPO_3 = GITHUB.get_repo(TEST_REPO_3)
TEST_REPO_NUMBER_OF_PULLS = PYGIT_TEST_REPO.get_pulls('all').totalCount
TEST_REPO_2_NUMBER_OF_PULLS = PYGIT_TEST_REPO_2.get_pulls('all').totalCount
TEST_REPO_3_NUMBER_OF_PULLS = PYGIT_TEST_REPO_3.get_pulls('all').totalCount
ZERO, ONE, TWO, THREE = 0, 1, 2, 3

mongo_test_init() # Tell the mining script NOT to use the production mongo database

# Utility function for testing 
def initialize_batch_json(self, batch_list, repo_name):
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
        number_pull_requests = PULL_REQUESTS_COLLECTION.count_documents({})
        self.assertEqual(number_pull_requests, ZERO)

    def test_can_mine_pull_requests_from_repo(self):
        batch_data = batchify(PYGIT_TEST_REPO.full_name.lower())
        self.initialize_batch_json(batch_data, PYGIT_TEST_REPO.full_name.lower())
        for batch_job in range(len(batch_data)):
            pulls_batch = get_batch_number(PYGIT_TEST_REPO.full_name.lower(), batch_job)
            mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO.full_name.lower())

        number_pull_requests = PULL_REQUESTS_COLLECTION.count_documents({})
        self.assertEqual(number_pull_requests, TEST_REPO_NUMBER_OF_PULLS)

    def test_mining_pull_requests_twice_from_repo_doesnt_count_as_separate_entries(self):
        batch_data_one = batchify(PYGIT_TEST_REPO.full_name.lower())
        self.initialize_batch_json(batch_data_one, PYGIT_TEST_REPO.full_name.lower())

        for batch_job in range(len(batch_data_one)):
            pulls_batch = get_batch_number(PYGIT_TEST_REPO.full_name.lower(), batch_job)
            mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO.full_name.lower())
            mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO.full_name.lower())
        
            
        
        number_pull_requests = PULL_REQUESTS_COLLECTION.count_documents({})
        self.assertEqual(number_pull_requests, TEST_REPO_NUMBER_OF_PULLS)

    def test_can_mine_two_separate_repos_pull_requests(self):
        batch_data_one = batchify(PYGIT_TEST_REPO.full_name.lower())
        self.initialize_batch_json(batch_data_one, PYGIT_TEST_REPO.full_name.lower())

        for batch_job in range(len(batch_data_one)):
            pulls_batch = get_batch_number(PYGIT_TEST_REPO.full_name.lower(), batch_job)
            mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO.full_name.lower())
            mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO.full_name.lower())

        batch_data_two = batchify(PYGIT_TEST_REPO_3.full_name.lower())
        self.initialize_batch_json(batch_data_two, PYGIT_TEST_REPO_3.full_name.lower())

        for batch_job in range(len(batch_data_one)):
            pulls_batch = get_batch_number(PYGIT_TEST_REPO_3.full_name.lower(), batch_job)
            mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO_3.full_name.lower())
            mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO_3.full_name.lower())

        number_pull_requests = PULL_REQUESTS_COLLECTION.count_documents({})
        total_prs = TEST_REPO_NUMBER_OF_PULLS + TEST_REPO_3_NUMBER_OF_PULLS
        self.assertEqual(number_pull_requests, total_prs)

    def test_can_find_pulls_belonging_to_specific_repo(self):
        batch_data_one = batchify(PYGIT_TEST_REPO.full_name.lower())
        self.initialize_batch_json(batch_data_one, PYGIT_TEST_REPO.full_name.lower())

        for batch_job in range(len(batch_data_one)):
            pulls_batch = get_batch_number(PYGIT_TEST_REPO.full_name.lower(), batch_job)
            mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO.full_name.lower())
            mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO.full_name.lower())

        batch_data_two = batchify(PYGIT_TEST_REPO_3.full_name.lower())
        self.initialize_batch_json(batch_data_two, PYGIT_TEST_REPO_3.full_name.lower())

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
        self.initialize_batch_json(batch_data_one, PYGIT_TEST_REPO.full_name.lower())

        for batch_job in range(len(batch_data_one)):
            pulls_batch = get_batch_number(PYGIT_TEST_REPO.full_name.lower(), batch_job)
            mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO.full_name.lower())
            mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO.full_name.lower())

        batch_data_two = batchify(PYGIT_TEST_REPO_3.full_name.lower())
        self.initialize_batch_json(batch_data_two, PYGIT_TEST_REPO_3.full_name.lower())

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
        self.initialize_batch_json(batch_data_one, PYGIT_TEST_REPO.full_name.lower())

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
        self.initialize_batch_json(batch_data_one, PYGIT_TEST_REPO_2.full_name.lower())

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
        self.initialize_batch_json(batch_data_one, PYGIT_TEST_REPO.full_name.lower())

        for batch_job in range(len(batch_data_one)):
            pulls_batch = get_batch_number(PYGIT_TEST_REPO.full_name.lower(), batch_job)
            mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO.full_name.lower())
            mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO.full_name.lower())

        batch_data_two = batchify(PYGIT_TEST_REPO_2.full_name.lower())
        self.initialize_batch_json(batch_data_two, PYGIT_TEST_REPO_2.full_name.lower())

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
        self.initialize_batch_json(batch_data_one, PYGIT_TEST_REPO.full_name.lower())

        for batch_job in range(len(batch_data_one)):
            pulls_batch = get_batch_number(PYGIT_TEST_REPO.full_name.lower(), batch_job)
            mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO.full_name.lower())
            mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO.full_name.lower())

        batch_data_two = batchify(PYGIT_TEST_REPO_3.full_name.lower())
        self.initialize_batch_json(batch_data_two, PYGIT_TEST_REPO_3.full_name.lower())

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
        self.initialize_batch_json(batch_data_one, PYGIT_TEST_REPO.full_name.lower())

        for batch_job in range(len(batch_data_one)):
            pulls_batch = get_batch_number(PYGIT_TEST_REPO.full_name.lower(), batch_job)
            mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO.full_name.lower())
            mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO.full_name.lower())

        batch_data_two = batchify(PYGIT_TEST_REPO_3.full_name.lower())
        self.initialize_batch_json(batch_data_two, PYGIT_TEST_REPO_3.full_name.lower())

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
        self.initialize_batch_json(batch_data_one, PYGIT_TEST_REPO.full_name.lower())

        for batch_job in range(len(batch_data_one)):
            pulls_batch = get_batch_number(PYGIT_TEST_REPO.full_name.lower(), batch_job)
            mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO.full_name.lower())
            mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO.full_name.lower())

        batch_data_two = batchify(PYGIT_TEST_REPO_3.full_name.lower())
        self.initialize_batch_json(batch_data_two, PYGIT_TEST_REPO_3.full_name.lower())

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

    init_batch = initialize_batch_json

    def tearDown(self):
        delete_all_repos_from_repo_collection()
        delete_all_pulls_from_pull_request_collection()
        delete_all_pull_requests_batches_from_batch_collection()
    
    def test_can_delete_all_repos_and_pulls_in_one_call(self):
        batch_data_one = batchify(PYGIT_TEST_REPO.full_name.lower())
        self.init_batch(batch_data_one, PYGIT_TEST_REPO.full_name.lower())

        for batch_job in range(len(batch_data_one)):
            pulls_batch = get_batch_number(PYGIT_TEST_REPO.full_name.lower(), batch_job)
            mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO.full_name.lower())
            mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO.full_name.lower())

        batch_data_two = batchify(PYGIT_TEST_REPO_3.full_name.lower())
        self.init_batch(batch_data_two, PYGIT_TEST_REPO_3.full_name.lower())

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
        self.init_batch(batch_data_one, PYGIT_TEST_REPO.full_name.lower())

        for batch_job in range(len(batch_data_one)):
            pulls_batch = get_batch_number(PYGIT_TEST_REPO.full_name.lower(), batch_job)
            mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO.full_name.lower())
            mine_pulls_batch(pulls_batch, PYGIT_TEST_REPO.full_name.lower())

        batch_data_two = batchify(PYGIT_TEST_REPO_3.full_name.lower())
        self.init_batch(batch_data_two, PYGIT_TEST_REPO_3.full_name.lower())

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
