# coding: utf-8
from __future__ import unicode_literals
import unittest
import os
import time
from choppy.core.cromwell import Cromwell
import choppy.config as c
import datetime
import requests


class CromwellUnitTests(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        resources = c.resource_dir
        self.cromwell = Cromwell(host='btl-cromwell')
        self.json = os.path.join(resources, 'hello.json')
        self.wdl = os.path.join(resources, 'hello_world.wdl')
        self.labels = {'username': 'amr', 'foo': 'bar'}

    def _initiate_workflow(self):
        wf = self.cromwell.jstart_workflow(self.wdl, self.json)
        time.sleep(5)
        return wf

    def test_start_workflow(self):
        wf = self._initiate_workflow()
        wfid = wf['id']
        self.assertTrue('id' in wf and 'status' in wf)
        self.assertEqual(wf['status'], 'Submitted')
        self.assertEqual(len(wfid), 36)
        self.cromwell.stop_workflow(wfid)

    def test_build_long_url(self):
        wf = self._initiate_workflow()
        wfid = wf['id']
        url_dict = {
            'name': 'test_build_long_url',
            'id': wfid,
            'start': datetime.datetime.now() - datetime.timedelta(days=1),
            'end': datetime.datetime.now()
        }
        query_url = self.cromwell.build_query_url(
            'http://btl-cromwell:9000/api/workflows/v1/query?', url_dict)
        r = requests.get(query_url)
        self.assertEquals(r.status_code, 200)
        self.cromwell.stop_workflow(wfid)

    def test_label_workflow(self):
        wf = self._initiate_workflow()
        wfid = wf['id']
        r = self.cromwell.label_workflow(wfid, self.labels)
        self.assertEquals(r.status_code, 200)
        self.cromwell.stop_workflow(wfid)

    def test_explain(self):
        wf = self._initiate_workflow()
        wfid = wf['id']
        time.sleep(10)
        result = self.cromwell.explain_workflow(wfid)
        self.assertIsInstance(result, tuple)
        self.cromwell.stop_workflow(wfid)

    def test_stop_workflow(self):
        wf = self._initiate_workflow()
        wfid = wf['id']
        result = self.cromwell.stop_workflow(wfid)
        print(result)
        self.cromwell.stop_workflow(wfid)

    @classmethod
    def tearDownClass(self):
        print("Done!")
