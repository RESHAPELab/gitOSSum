from mining import *
import unittest


# Setup all variables for testing, ensure mongod is running in the background 
MONGO_CLIENT = MongoClient('localhost', 27017) # Where are we connecting
DB = MONGO_CLIENT.backend_db # The specific mongo database we are working with 
REPOS_COLLECTION = db.repos # collection for storing all of a repo's main api json information 
PULL_REQUESTS_COLLECTION = db.pullRequests # collection for storing all pull requests for all repos 
TEST_REPO = "swhite9478/github-mining-tool" # repo for testing purposes 
GITHUB = Github("Githubfake01", "5RNsya*z#&aA", per_page=100) # authorization for the github API
PYGIT_TEST_REPO = GITHUB.get_repo(TEST_REPO) # Pygit's interpretation of the repo 


# Class to unit test the mining.py functionality 
class TestMiner(unittest.TestCase):

    # Test that we can remove all repos from the repos collection 
    def test_delete_all_from_repos_collection(self):
        print()
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

 
 
if __name__ == '__main__':
    unittest.main()