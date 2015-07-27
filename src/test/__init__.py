import unittest
from test.treetest import GeogigTreeTest
from test.testrepo import testRepo
from test.repotest import GeogigRepositoryTest
from test.featuretest import GeogigFeatureTest
from test.commitishtest import GeogigCommitishTest
from test.committest import GeogigCommitTest
from test.difftest import GeogigDiffTest


def suite():
    suite = unittest.makeSuite(GeogigTreeTest, 'test')
    suite.addTests(unittest.makeSuite(GeogigRepositoryTest, 'test'))
    suite.addTests(unittest.makeSuite(GeogigFeatureTest, 'test'))
    suite.addTests(unittest.makeSuite(GeogigCommitishTest, 'test'))
    suite.addTests(unittest.makeSuite(GeogigCommitTest, 'test'))
    suite.addTests(unittest.makeSuite(GeogigDiffTest, 'test'))
    return suite
