from mining import *
import re
import unittest


# Setup all variables for testing, ensure mongod is running in the background 
MONGO_CLIENT = MongoClient('localhost', 27017) # Where are we connecting
DB = MONGO_CLIENT.backend_db # The specific mongo database we are working with 
REPOS_COLLECTION = db.repos # collection for storing all of a repo's main api json information 
PULL_REQUESTS_COLLECTION = db.pullRequests # collection for storing all pull requests for all repos 
TEST_REPO = "swhite9478/github-mining-tool" # repo for testing purposes 
TEST_REPO_2 = 'google/gumbo-parser'
GITHUB = Github("Githubfake01", "5RNsya*z#&aA", per_page=100) # authorization for the github API
PYGIT_TEST_REPO = GITHUB.get_repo(TEST_REPO) # Pygit's interpretation of the repo 
PYGIT_TEST_REPO_2 = GITHUB.get_repo(TEST_REPO_2)


# Class to unit test the mining.py functionality 
class TestMiner(unittest.TestCase):

    def test_pygit_test_repo_not_none(self):
        self.assertIsNotNone(PYGIT_TEST_REPO)

    # Test that we can remove all repos from the repos collection 
    def test_delete_all_from_repos_collection(self):
        print()
        delete_all_repos_from_repo_collection()
        number_of_repos = REPOS_COLLECTION.count_documents({})
        self.assertEqual(number_of_repos, 0)

    def test_delete_all_from_repos_collection_twice(self):
        print()
        delete_all_repos_from_repo_collection()
        delete_all_repos_from_repo_collection()
        number_of_repos = REPOS_COLLECTION.count_documents({})
        self.assertEqual(number_of_repos, 0)

    def test_can_mine_one_repo_and_store_in_database(self):
        print()
        delete_all_repos_from_repo_collection()
        mine_repo_page(PYGIT_TEST_REPO)
        number_of_repos = REPOS_COLLECTION.count_documents({})
        self.assertEqual(number_of_repos, 1)

    def test_can_mine_one_repo_and_remove_from_database(self):
        print()
        delete_all_repos_from_repo_collection()
        mine_repo_page(PYGIT_TEST_REPO)
        delete_all_repos_from_repo_collection()
        number_of_repos = REPOS_COLLECTION.count_documents({})
        self.assertEqual(number_of_repos, 0)

    def test_mining_same_repo_page_twice_doesnt_count_as_two_entries(self):
        print()
        delete_all_repos_from_repo_collection()
        mine_repo_page(PYGIT_TEST_REPO)
        mine_repo_page(PYGIT_TEST_REPO)
        number_of_repos = REPOS_COLLECTION.count_documents({})
        self.assertEqual(number_of_repos, 1)

    def test_mining_same_repo_page_three_times_doesnt_count_as_three_entries(self):
        print()
        delete_all_repos_from_repo_collection()
        mine_repo_page(PYGIT_TEST_REPO)
        mine_repo_page(PYGIT_TEST_REPO)
        mine_repo_page(PYGIT_TEST_REPO)
        number_of_repos = REPOS_COLLECTION.count_documents({})
        self.assertEqual(number_of_repos, 1)

    def test_can_mine_two_repo_pages(self):
       print()
       delete_all_repos_from_repo_collection()
       mine_repo_page(PYGIT_TEST_REPO)
       mine_repo_page(PYGIT_TEST_REPO_2)
       number_of_repos = REPOS_COLLECTION.count_documents({})
       self.assertEqual(number_of_repos, 2)

    def test_mining_two_repo_pages_twice_doesnt_count_as_four_entries(self):
       print()
       delete_all_repos_from_repo_collection()
       mine_repo_page(PYGIT_TEST_REPO)
       mine_repo_page(PYGIT_TEST_REPO_2)
       mine_repo_page(PYGIT_TEST_REPO)
       mine_repo_page(PYGIT_TEST_REPO_2)
       number_of_repos = REPOS_COLLECTION.count_documents({})
       self.assertEqual(number_of_repos, 2)


    def test_find_repo_main_page(self):
        print()
        delete_all_repos_from_repo_collection()
        mine_repo_page(PYGIT_TEST_REPO)
        test_repo_found = find_repo_main_page(TEST_REPO)
        self.assertEqual(test_repo_found["full_name"], PYGIT_TEST_REPO.full_name)

    def test_find_repo_main_page_created_at_attribute(self):
        print()
        delete_all_repos_from_repo_collection()
        mine_repo_page(PYGIT_TEST_REPO)
        test_repo_found = find_repo_main_page(TEST_REPO)
        created_at = tuple(int(num) for num in (re.split('-|T|:|Z', test_repo_found["created_at"]))[:-1])
        pygit_test_repo_created_at = tuple(int(num) for num in (re.split('-| |:', str(PYGIT_TEST_REPO.created_at))))
        self.assertEqual(created_at, pygit_test_repo_created_at)

    def test_find_repo_main_page_owner_login_attribute(self):
        print()
        delete_all_repos_from_repo_collection()
        mine_repo_page(PYGIT_TEST_REPO)
        test_repo_found = find_repo_main_page(TEST_REPO)
        self.assertEqual(test_repo_found['owner']['login'], PYGIT_TEST_REPO.owner.login)

    def test_can_find_and_delete_specifc_repo_from_repo_collection(self):
        print()
        delete_all_repos_from_repo_collection()
        mine_repo_page(PYGIT_TEST_REPO)
        mine_repo_page(PYGIT_TEST_REPO_2)
        delete_specific_repo_from_repo_collection(TEST_REPO)
        number_of_repos = REPOS_COLLECTION.count_documents({})
        self.assertEqual(number_of_repos, 1)


    def test_can_delete_all_from_pull_requests_collection(self):
        print()
        delete_all_pulls_from_pull_request_collection()
        number_pull_requests = PULL_REQUESTS_COLLECTION.count_documents({})
        self.assertEqual(number_pull_requests, 0)
 
if __name__ == '__main__':
    unittest.main()