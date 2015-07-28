import os
import time
import unittest
import datetime

from geogigpy import geogig
from geogigpy.osmmapping import OSMMapping, OSMMappingRule
from geogigpy.geometry import Geometry
from geogigpy.repo import Repository
from geogigpy.geogigexception import GeoGigException, GeoGigConflictException
from geogigpy.commitish import Commitish
from geogigpy.diff import TYPE_MODIFIED
from geogigpy.feature import Feature
from test.testrepo import testRepo


class GeogigRepositoryTest(unittest.TestCase):

    repo = testRepo()

    def getTempRepoPath(self):
        return os.path.join(os.path.dirname(__file__), "temp",
                            str(time.time())).replace('\\', '/')

    def getClonedRepo(self):
        dst = self.getTempRepoPath()
        return self.repo.clone(dst)

    def testCreateEmptyRepo(self):
        repoPath = self.getTempRepoPath()
        Repository(repoPath, init=True)

    def testRevParse(self):
        headid = self.repo.revparse(geogig.HEAD)
        entries = self.repo.log()
        self.assertEqual(entries[0].commitid, headid)

    def testHead(self):
        head = self.repo.head
        self.assertEqual("master", head.ref)

    def testIsDetached(self):
        repo = self.getClonedRepo()
        self.assertFalse(repo.isdetached())
        log = repo.log()
        repo.checkout(log[1].ref)
        self.assertTrue(repo.isdetached())

    def testRevParseWrongReference(self):
        try:
            self.repo.revparse("WrOnGReF")
            self.fail()
        except GeoGigException as e:
            pass

    def testLog(self):
        commits = self.repo.log()
        self.assertEqual(4, len(commits))
        self.assertEqual("message_4", commits[0].message)
        self.assertEqual("user", commits[0].authorname)
        # TODO: add more

    def testLogInBranch(self):
        entries = self.repo.log("conflicted")
        self.assertEqual(4, len(entries))

    def testCommitAtDate(self):
        now = datetime.datetime.utcnow()
        commit = self.repo.commitatdate(now)
        log = self.repo.log()
        # self.assertEquals(log[0].message, commit.message)

    def testCommitAtWrongDate(self):
        epoch = datetime.datetime.utcfromtimestamp(0)
        try:
            commit = self.repo.commitatdate(epoch)
            self.fail()
        except GeoGigException as e:
            self.assertTrue("Invalid date" in e.args[0])

    def testLogEmptyRepo(self):
        repoPath = self.getTempRepoPath()
        repo = Repository(repoPath, init=True)
        log = repo.log()
        self.assertFalse(log)

    def testTreesAtHead(self):
        trees = self.repo.trees
        self.assertEqual(1, len(trees))
        self.assertEqual("parks", trees[0].path)
        self.assertEqual(geogig.HEAD, trees[0].ref)

    def testTreesAtCommit(self):
        head = self.repo.head
        parent = head.parent
        trees = parent.root.trees
        self.assertEqual(1, len(trees))
        self.assertEqual("parks", trees[0].path)
        entries = self.repo.log()
        id = self.repo.revparse(trees[0].ref)
        self.assertEqual(entries[1].commitid, id)

    def testFeaturesAtHead(self):
        features = self.repo.features(path="parks")
        self.assertEqual(5, len(features))
        feature = features[0]
        self.assertEqual("parks/5", feature.path)
        self.assertEqual("HEAD", feature.ref)

    def testChildren(self):
        children = self.repo.children()
        self.assertEqual(1, len(children))
        # TODO improve this test

    def testDiff(self):
        repo = self.getClonedRepo()
        diffs = repo.diff("master", Commitish(self.repo, "master").parent.ref)
        self.assertEqual(1, len(diffs))
        self.assertEqual("parks/5", diffs[0].path)
        self.assertEqual(TYPE_MODIFIED, diffs[0].type())

    def testDiffWithPath(self):
        repo = self.getClonedRepo()
        diffs = repo.diff("HEAD", "HEAD~3")
        self.assertEqual(2, len(diffs))
        diffs = repo.diff("HEAD", "HEAD~3", "parks/5")
        self.assertEqual(1, len(diffs))

    def testFeatureData(self):
        data = self.repo.featuredata(geogig.HEAD, "parks/1")
        self.assertEqual(8, len(data))
        self.assertEqual("Public", data["usage"][0])
        self.assertTrue("owner" in data)
        self.assertTrue("agency" in data)
        self.assertTrue("name" in data)
        self.assertTrue("parktype" in data)
        self.assertTrue("area" in data)
        self.assertTrue("perimeter" in data)
        self.assertTrue("the_geom" in data)
        self.assertTrue(isinstance(data["the_geom"][0], Geometry))

    def testFeatureDataNonExistentFeature(self):
        return
        try:
            self.repo.featuredata(geogig.HEAD, "wrongpath/wrongname")
            self.fail()
        except GeoGigException as e:
            pass

    def testAddAndCommit(self):
        repo = self.getClonedRepo()
        log = repo.log()
        self.assertEqual(4, len(log))
        path = os.path.join(os.path.dirname(__file__),
                            "data", "shp", "1", "parks.shp")
        repo.importshp(path)
        repo.add()
        unstaged = repo.unstaged()
        self.assertFalse(unstaged)
        staged = repo.staged()
        self.assertTrue(staged)
        repo.commit("message")
        staged = repo.staged()
        self.assertFalse(staged)
        log = repo.log()
        self.assertEqual(5, len(log))
        self.assertTrue("message", log[4].message)

    def testCommitWithMessageWithBlankSpaces(self):
        repo = self.getClonedRepo()
        log = repo.log()
        self.assertEqual(4, len(log))
        path = os.path.join(os.path.dirname(__file__),
                            "data", "shp", "1", "parks.shp")
        repo.importshp(path)
        repo.add()
        unstaged = repo.unstaged()
        self.assertFalse(unstaged)
        staged = repo.staged()
        self.assertTrue(staged)
        commit_msg = "A message with blank spaces\nand a line break"
        repo.commit(commit_msg)
        staged = repo.staged()
        self.assertFalse(staged)
        log = repo.log()
        self.assertEqual(5, len(log))
        self.assertTrue(commit_msg, log[4].message)

    def testCreateReadAndDeleteBranch(self):
        repo = self.getClonedRepo()
        branches = repo.branches
        self.assertEqual(3, len(branches))
        repo.createbranch(geogig.HEAD, "anewbranch")
        branches = repo.branches
        self.assertEqual(4, len(branches))
        self.assertTrue("anewbranch" in branches)
        repo.deletebranch("anewbranch")
        branches = repo.branches
        self.assertEqual(3, len(branches))
        self.assertFalse("anewbranch" in branches)

    def testBlame(self):
        feature = self.repo.feature(geogig.HEAD, "parks/5")
        blame = self.repo.blame("parks/5")
        self.assertEqual(8, len(blame))
        attrs = feature.attributes
        for k, v in blame.items():
            self.assertTrue(v[0], attrs[k])

    def testVersions(self):
        versions = self.repo.versions("parks/5")
        self.assertEqual(2, len(versions))

    def testFeatureDiff(self):
        diff = self.repo.featurediff(geogig.HEAD, geogig.HEAD + "~1", "parks/5")
        self.assertEqual(2, len(diff))
        self.assertTrue("area" in diff)

    def testCreateReadAndDeleteTag(self):
        repo = self.getClonedRepo()
        tags = repo.tags
        self.assertEqual(0, len(tags))
        self.repo.createtag(self.repo.head.ref, "anewtag", "message1")
        tags = self.repo.tags
        self.assertEqual(1, len(tags))
        self.assertTrue("anewtag" in tags)
        self.repo.deletetag("anewtag")
        tags = self.repo.tags
        self.assertEqual(0, len(tags))

    def testModifyFeature(self):
        repo = self.getClonedRepo()
        attrs = Feature(repo, geogig.HEAD, "parks/1").attributes
        attrs["area"] = 1234.5
        repo.insertfeature("parks/1", attrs)
        attrs = Feature(repo, geogig.WORK_HEAD, "parks/1").attributes
        self.assertEqual(1234.5, attrs["area"])

    def testAddFeature(self):
        nfeats = "parks/newfeature"
        repo = self.getClonedRepo()
        attrs = Feature(repo, geogig.HEAD, "parks/1").attributes
        repo.insertfeature(nfeats, attrs)
        newattrs = Feature(repo, geogig.WORK_HEAD, nfeats).attributes
        self.assertAlmostEqual(attrs["area"], newattrs["area"], 5)

    def testRemoveFeature(self):
        repo = self.getClonedRepo()
        repo.removefeatures(["parks/1"])
        f = Feature(repo, geogig.WORK_HEAD, "parks/1")
        self.assertFalse(f.exists())
        f = Feature(repo, geogig.STAGE_HEAD, "parks/1")
        self.assertFalse(f.exists())

    def testConflicts(self):
        repo = self.getClonedRepo()
        try:
            repo.merge("conflicted")
            self.fail()
        except GeoGigConflictException as e:
            pass
        conflicts = repo.conflicts()
        self.assertEqual(1, len(conflicts))
        log = repo.log()
        conflicted = repo.revparse("conflicted")
        self.assertEqual(log[1].ref, conflicts["parks/5"][0].ref)
        self.assertEqual(log[0].ref, conflicts["parks/5"][1].ref)
        self.assertEqual(conflicted, conflicts["parks/5"][2].ref)

    def testSolveConflict(self):
        repo = self.getClonedRepo()
        try:
            repo.merge("conflicted")
            self.fail()
        except GeoGigConflictException as e:
            pass
        conflicts = repo.conflicts()
        self.assertEqual(1, len(conflicts))
        path = list(conflicts.keys())[0]
        self.assertTrue("parks/5", path)
        features = conflicts[path]
        origFeature = features[0]
        repo.solveconflict(path, origFeature.attributes)
        conflicts = repo.conflicts()
        self.assertEqual(0, len(conflicts))
        feature = Feature(repo, geogig.WORK_HEAD, "parks/5")
        self.assertAlmostEqual(feature.attributes["area"],
                               origFeature.attributes["area"], 5)

    def testSolveConflictOurs(self):
        repo = self.getClonedRepo()
        try:
            repo.merge("conflicted")
            self.fail()
        except GeoGigConflictException as e:
            pass
        conflicts = repo.conflicts()
        self.assertEqual(1, len(conflicts))
        path = list(conflicts.keys())[0]
        self.assertTrue("parks/5", path)
        features = conflicts[path]
        oursFeature = features[1]
        repo.solveconflicts([path], geogig.OURS)
        conflicts = repo.conflicts()
        self.assertEqual(0, len(conflicts))
        feature = Feature(repo, geogig.WORK_HEAD, "parks/5")
        self.assertEqual(feature.attributes["area"],
                         oursFeature.attributes["area"])

    def testSolveConflictTheirs(self):
        repo = self.getClonedRepo()
        try:
            repo.merge("conflicted")
            self.fail()
        except GeoGigConflictException as e:
            pass
        conflicts = repo.conflicts()
        self.assertEqual(1, len(conflicts))
        path = list(conflicts.keys())[0]
        self.assertTrue("parks/5", path)
        features = conflicts[path]
        theirsFeature = features[2]
        repo.solveconflicts([path], geogig.THEIRS)
        conflicts = repo.conflicts()
        self.assertEqual(0, len(conflicts))
        feature = Feature(repo, geogig.WORK_HEAD, "parks/5")
        self.assertEqual(feature.attributes["area"],
                         theirsFeature.attributes["area"])

    def testIsMerging(self):
        repo = self.getClonedRepo()
        try:
            repo.merge("conflicted")
            self.fail()
        except GeoGigConflictException as e:
            pass
        self.assertTrue(repo.ismerging())
        repo.abort()
        self.assertFalse(repo.ismerging())

    def testIsRebasing(self):
        repo = self.getClonedRepo()
        try:
            repo.rebase("conflicted")
            self.fail()
        except GeoGigConflictException as e:
            pass
        self.assertTrue(repo.isrebasing())
        repo.abort()
        self.assertFalse(repo.isrebasing())

    def testMergeAndResolveConflict(self):
        repo = self.getClonedRepo()
        try:
            repo.merge("conflicted")
            self.fail()
        except GeoGigConflictException as e:
            self.assertTrue("conflict" in e.args[0])
        conflicts = repo.conflicts()
        self.assertEqual(1, len(conflicts))
        iter(conflicts.values()).next()[0].setascurrent()
        conflicts = repo.conflicts()
        self.assertEqual(0, len(conflicts))

    def testContinueRebasing(self):
        repo = self.getClonedRepo()
        try:
            repo.rebase("conflicted")
            self.fail()
        except GeoGigConflictException as e:
            self.assertTrue("conflict" in e.args[0])
        conflicts = repo.conflicts()
        self.assertEqual(1, len(conflicts))
        iter(conflicts.values()).next()[0].setascurrent()
        repo.continue_()

    def testCantContinueRebasing(self):
        repo = self.getClonedRepo()
        try:
            repo.rebase("conflicted")
            self.fail()
        except GeoGigConflictException as e:
            self.assertTrue("conflict" in e.args[0])
        conflicts = repo.conflicts()
        self.assertEqual(1, len(conflicts))
        try:
            repo.continue_()
            self.fail()
        except GeoGigException as e:
            pass

    def testRebase(self):
        repo = self.getClonedRepo()
        log = repo.log()
        repo.rebase("unconflicted")
        newlog = repo.log()
        self.assertEqual(log[0].message, newlog[0].message)
        self.assertEqual(len(log) + 1, len(newlog))

    def testMerge(self):
        repo = self.getClonedRepo()
        commitid = repo.revparse("unconflicted")
        repo.merge("unconflicted")
        log = repo.log()
        self.assertEqual(commitid, log[1].ref)

    def testMergeNoCommit(self):
        repo = self.getClonedRepo()
        log = repo.log()
        ref = log[0].ref
        repo.merge("unconflicted", nocommit=True)
        self.assertTrue(repo.staged())
        log = repo.log()
        self.assertEqual(ref, log[0].ref)

    def testRemotes(self):
        repo = self.getClonedRepo()
        remotes = repo.remotes
        self.assertEqual(1, len(remotes))
        repo.addremote("myremote", "http://myremoteurl.com", "user", "pass")
        remotes = repo.remotes
        self.assertTrue("myremote" in remotes)
        repo.removeremote("myremote")
        remotes = repo.remotes
        self.assertEqual(1, len(remotes))
        self.assertFalse("myremote" in remotes)

    def testCherryPick(self):
        repo = self.getClonedRepo()
        commitid = repo.revparse("unconflicted")
        repo.cherrypick("unconflicted")
        log = repo.log()
        self.assertTrue(commitid, log[0].ref)

    def testCherryPickWithConflicts(self):
        repo = self.getClonedRepo()
        log = repo.log()
        ref = log[0].ref
        try:
            repo.cherrypick("conflicted")
            self.fail()
        except GeoGigException as e:
            self.assertTrue("conflict" in e.args[0])
        log = repo.log()
        self.assertTrue(ref, log[0].ref)

    def testOsmImport(self):
        repoPath = self.getTempRepoPath()
        repo = Repository(repoPath, init=True)
        osmfile = os.path.join(os.path.dirname(__file__),
                               "data", "osm", "ways.xml")
        repo.importosm(osmfile)
        feature = Feature(repo, geogig.WORK_HEAD, "way/31045880")
        self.assertTrue(feature.exists())

    def testOsmImportWithMappingFile(self):
        repoPath = self.getTempRepoPath()
        repo = Repository(repoPath, init=True)
        osmfile = os.path.join(os.path.dirname(__file__),
                               "data", "osm", "ways.xml")
        mappingfile = os.path.join(os.path.dirname(__file__),
                                   "data", "osm", "mapping.json")
        repo.importosm(osmfile, False, mappingfile)
        feature = Feature(repo, geogig.WORK_HEAD, "onewaystreets/31045880")
        self.assertTrue(feature.exists())

    def testOsmImportWithMapping(self):
        mapping = OSMMapping()
        rule = OSMMappingRule("onewaystreets")
        rule.addfilter("oneway", "yes")
        rule.addfield("lit", "lit", geogig.TYPE_STRING)
        rule.addfield("geom", "the_geom", geogig.TYPE_LINESTRING)
        mapping.addrule(rule)
        repoPath = self.getTempRepoPath()
        repo = Repository(repoPath, init=True)
        osmfile = os.path.join(os.path.dirname(__file__),
                               "data", "osm", "ways.xml")
        repo.importosm(osmfile, False, mapping)
        feature = Feature(repo, geogig.WORK_HEAD, "onewaystreets/31045880")
        self.assertTrue(feature.exists())

    def testOsmMapping(self):
        repoPath = self.getTempRepoPath()
        repo = Repository(repoPath, init=True)
        osmfile = os.path.join(os.path.dirname(__file__),
                               "data", "osm", "ways.xml")
        mappingfile = os.path.join(os.path.dirname(__file__),
                                   "data", "osm", "mapping.json")
        repo.importosm(osmfile)
        repo.add()
        repo.commit("message")
        repo.maposm(mappingfile)
        feature = Feature(repo, geogig.WORK_HEAD, "onewaystreets/31045880")
        self.assertTrue(feature.exists())

    def testConfig(self):
        repo = self.getClonedRepo()
        repo.config(geogig.USER_NAME, "mytestusername")
        repo.config(geogig.USER_EMAIL, "mytestuseremail@email.com")
        username = repo.getconfig(geogig.USER_NAME)
        self.assertTrue("mytestusername", username)
        email = repo.getconfig(geogig.USER_EMAIL)
        self.assertTrue("mytestuseremail@email.com", email)

    def testShow(self):
        text = self.repo.show(geogig.HEAD)
        self.assertTrue('user' in text)
        self.assertTrue('message_4' in text)

    def testPull(self):
        cloned = self.getClonedRepo()
        cloned2 = self.getClonedRepo()
        path = os.path.join(os.path.dirname(__file__),
                            "data", "shp", "1", "parks.shp")
        cloned.importshp(path)
        cloned.addandcommit("new_message")
        cloned2.pull("origin", geogig.MASTER)
        log = cloned2.log()
        self.assertTrue("new_message", log[0].message)

    def testPush(self):
        cloned = self.getClonedRepo()
        cloned2 = self.getClonedRepo()
        path = os.path.join(os.path.dirname(__file__),
                            "data", "shp", "1", "parks.shp")
        cloned2.importshp(path)
        cloned2.addandcommit("new_message")
        cloned.push("origin", geogig.MASTER)
        log = cloned.log()
        self.assertTrue("new_message", log[0].message)

    def testCount(self):
        count = self.repo.count(geogig.HEAD, "parks")
        self.assertEqual(5, count)

    def testResetHard(self):
        repo = self.getClonedRepo()
        repo.reset(repo.head.parent.ref, geogig.RESET_MODE_HARD)
        self.assertEqual("message_3", repo.log()[0].message)
        self.assertFalse(len(repo.unstaged()) > 0)

    def testResetMixed(self):
        repo = self.getClonedRepo()
        repo.reset(repo.head.parent.ref, geogig.RESET_MODE_MIXED)
        self.assertEqual("message_3", repo.log()[0].message)
        self.assertTrue(len(repo.unstaged()) > 0)

    def testFeatureType(self):
        repo = self.getClonedRepo()
        ftype = repo.featuretype(geogig.HEAD, "parks")
        self.assertEqual("DOUBLE", ftype["perimeter"])
        self.assertEqual("STRING", ftype["name"])
        self.assertEqual("MULTIPOLYGON", ftype["the_geom"])

    def testSynced(self):
        repo = self.getClonedRepo()
        path = os.path.join(os.path.dirname(__file__),
                            "data", "shp", "1", "parks.shp")
        repo.importshp(path)
        repo.add()
        unstaged = repo.unstaged()
        self.assertFalse(unstaged)
        staged = repo.staged()
        self.assertTrue(staged)
        repo.commit("message")
        log = repo.log()
        self.assertEqual(5, len(log))
        ahead, behind = repo.synced()
        self.assertEqual(1, ahead)
        self.assertEqual(0, behind)


