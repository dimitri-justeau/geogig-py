import unittest
import os
import time

from geogigpy import geogig
from geogigpy.commitish import Commitish
from test.testrepo import testRepo


class GeogigCommitishTest(unittest.TestCase):

    repo = testRepo()

    def getTempPath(self):
        return os.path.join(os.path.dirname(__file__), "temp",
                            str(time.time())).replace('\\', '/')

    def getClonedRepo(self):
        dst = self.getTempPath()
        return self.repo.clone(dst)

    def testLog(self):
        commitish = Commitish(self.repo, geogig.HEAD)
        log = commitish.log()
        self.assertEqual(4, len(log))
        self.assertEqual("message_4", log[0].message)

    def testRootTreeListing(self):
        commitish = Commitish(self.repo, geogig.HEAD)
        trees = commitish.root.trees
        self.assertEqual(1, len(trees))
        self.assertEqual("parks", trees[0].path)
        entries = self.repo.log()
        id = self.repo.revparse(trees[0].ref)
        self.assertEqual(entries[0].commitid, id)

    def testCheckout(self):
        repo = self.getClonedRepo()
        branch = Commitish(repo, "conflicted")
        branch.checkout()
        self.assertEqual(repo.head.id, branch.id)
        master = Commitish(repo, geogig.MASTER)
        master.checkout()
        self.assertEqual(repo.head.id, master.id)

    def testDiff(self):
        commitish = Commitish(self.repo, geogig.HEAD)
        diff = commitish.diff()
        self.assertEqual(1, len(diff))
        self.assertEqual("parks/5", diff[0].path)

    def testDiffCaching(self):
        commitish = Commitish(self.repo, geogig.HEAD)
        diff = commitish.diff()
        self.assertEqual(diff, commitish._diff)
