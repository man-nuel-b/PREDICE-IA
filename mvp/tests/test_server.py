import json
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from pathlib import Path
from unittest.mock import patch
import server

class ServerSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        cls.saved=server.STATE
        server.STATE=Path(cls.temp.name)/'state.json'
        cls.httpd=ThreadingHTTPServer(('127.0.0.1',0),server.API)
        cls.thread=threading.Thread(target=cls.httpd.serve_forever,daemon=True);cls.thread.start()
        cls.url='http://127.0.0.1:'+str(cls.httpd.server_port)
    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown();cls.httpd.server_close();cls.thread.join(timeout=4)
        server.STATE=cls.saved
        cls.temp.cleanup()
    def request(self,path,obj=None):
        kwargs={} if obj is None else {'data':json.dumps(obj).encode(),'headers':{'Content-Type':'application/json'},'method':'POST'}
        req=Request(self.url+path,**kwargs)
        req.add_header('Host','127.0.0.1:'+str(self.httpd.server_port))
        with urlopen(req,timeout=3) as r:return json.loads(r.read())
    def test_health_and_analysis(self):
        self.assertTrue(self.request('/api/status')['ok'])
        self.assertIn('recommendations',self.request('/api/data')['analysis'])
        self.assertIn('kpis',self.request('/api/analyze',{'settings':{'review_days':5}})['analysis'])
    def test_import_and_persistence(self):
        orig=self.request('/api/data')
        self.request('/api/import',{'kind':'waste','rows':[]})
        self.assertEqual(self.request('/api/data')['datasets']['waste'],[])
        self.request('/api/reset',{})
        self.assertEqual(len(self.request('/api/data')['datasets']['waste']),len(orig['datasets']['waste']))
    def test_invalid_data_returns_400(self):
        with self.assertRaises(HTTPError) as c:self.request('/api/import',{'kind':'sales','rows':[{'bad':'field'}]})
        self.assertEqual(c.exception.code,400)
    def test_cross_origin_rejected(self):
        req=Request(self.url+'/api/reset',data=b'{}',headers={'Content-Type':'application/json','Origin':'https://evil.example'},method='POST')
        with self.assertRaises(HTTPError) as c:urlopen(req,timeout=3)
        self.assertEqual(c.exception.code,403)
    def test_path_traversal_rejected(self):
        with self.assertRaises(HTTPError) as c:urlopen(self.url+'/secret.txt',timeout=3)
        self.assertEqual(c.exception.code,404)

if __name__=='__main__':unittest.main()
