"""Servidor local de Predice-IA MVP. Sin autenticación: NO publicar en Internet.

Ejecutar: python server.py (únicamente 127.0.0.1:8765)
"""
from __future__ import annotations

import json
import os
import threading
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from demo import sample_data
from engine import InputError, analyze, validate_dataset
from decisions import prevention_report
from insights import insight_report

ROOT = Path(__file__).resolve().parent
WEB = ROOT / 'web'
STATE = ROOT / '.local' / 'datasets.json'
LOCK = threading.RLock()
MAX_BODY = 8 * 1024 * 1024
PORT = 8765
ASSETS = {'/':('index.html','text/html; charset=utf-8'),'/app.js':('app.js','text/javascript; charset=utf-8'),'/styles.css':('styles.css','text/css; charset=utf-8'),'/advanced.css':('advanced.css','text/css; charset=utf-8'),'/advanced-analytics.js':('advanced-analytics.js','text/javascript; charset=utf-8'),'/advanced-ui.js':('advanced-ui.js','text/javascript; charset=utf-8'),'/csv-import.js':('csv-import.js','text/javascript; charset=utf-8'),'/decisions-ui.js':('decisions-ui.js','text/javascript; charset=utf-8'),'/insights-ui.js':('insights-ui.js','text/javascript; charset=utf-8')}


def load_state():
    with LOCK:
        if STATE.exists():
            obj=json.loads(STATE.read_text(encoding='utf-8'))
            return {k:validate_dataset(k,obj.get(k,[])) for k in ('lots','sales','waste')}
        return sample_data()


def save_state(data):
    with LOCK:
        STATE.parent.mkdir(exist_ok=True)
        safe = {k:validate_dataset(k,data.get(k,[])) for k in ('lots','sales','waste')}
        temp=STATE.with_suffix('.tmp')
        try:
            with temp.open('w',encoding='utf-8') as f:
                json.dump(safe,f,ensure_ascii=False)
                f.flush();os.fsync(f.fileno())
            os.replace(temp,STATE)
        finally:
            temp.unlink(missing_ok=True)


class API(BaseHTTPRequestHandler):
    server_version='PrediceLocal/0.3'
    def log_message(self,fmt,*args):
        print('%s - %s'%(self.address_string(),fmt%args))

    def respond(self,data,status=200):
        b=json.dumps(data,ensure_ascii=False,allow_nan=False).encode()
        self.send_response(status)
        self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Content-Length',str(len(b)))
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('X-Frame-Options','DENY')
        self.end_headers();self.wfile.write(b)

    def local_request(self):
        host=self.headers.get('Host','').split(':')[0].lower()
        return host in ('127.0.0.1','localhost') and self.client_address[0] in ('127.0.0.1','::1')

    def do_GET(self):
        if not self.local_request():return self.respond({'error':'Solo acceso local'},403)
        url=urlsplit(self.path).path
        if url in ('/api/status','/api/data','/api/decisions','/api/insights'):
            try:
                data=load_state()
                if url=='/api/status':return self.respond({'ok':True,'mode':'local_mvp','today':date.today().isoformat()})
                if url=='/api/decisions':return self.respond({'decisions':prevention_report(data)})
                if url=='/api/insights':return self.respond({'insights':insight_report(data)})
                return self.respond({'datasets':data,'analysis':analyze(data)})
            except (ValueError,OSError) as exc:
                return self.respond({'error':'No se pudo cargar el estado local','detail':str(exc)},500)
        if url not in ASSETS:return self.respond({'error':'Ruta no encontrada'},404)
        name,mime=ASSETS[url];file=WEB/name
        body=file.read_bytes()
        self.send_response(200);self.send_header('Content-Type',mime)
        self.send_header('Content-Length',str(len(body)))
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Content-Security-Policy',"default-src 'self'; style-src 'self'; script-src 'self'; img-src 'self' data:; object-src 'none'; frame-ancestors 'none'; base-uri 'none'")
        self.end_headers();self.wfile.write(body)

    def do_POST(self):
        if not self.local_request():return self.respond({'error':'Solo acceso local'},403)
        if urlsplit(self.path).path not in ('/api/import','/api/analyze','/api/reset'):
            return self.respond({'error':'Ruta no encontrada'},404)
        origin=self.headers.get('Origin')
        if origin and origin not in ('http://localhost:8765','http://127.0.0.1:8765'):
            return self.respond({'error':'Origen no permitido'},403)
        if self.headers.get('Content-Type','').split(';')[0].strip()!='application/json':
            return self.respond({'error':'Enviar JSON'},415)
        try:
            length=int(self.headers.get('Content-Length','0'))
            if not 0<=length<=MAX_BODY:return self.respond({'error':'Tamaño no permitido'},413)
            payload=json.loads(self.rfile.read(length))
            if not isinstance(payload,dict):raise InputError('Objeto JSON requerido')
            path=urlsplit(self.path).path
            if path=='/api/reset':
                data=sample_data();save_state(data)
            elif path=='/api/import':
                kind=payload.get('kind')
                if kind not in ('lots','sales','waste'):raise InputError('Tipo de importación desconocido')
                rows=validate_dataset(kind,payload.get('rows'))
                with LOCK:
                    data=load_state();data[kind]=rows;save_state(data)
            else:
                data=load_state()
            report=analyze(data,payload.get('settings') if path=='/api/analyze' else None)
            return self.respond({'datasets':data,'analysis':report})
        except (InputError,ValueError,TypeError,json.JSONDecodeError) as exc:
            return self.respond({'error':str(exc)},400)
        except (OSError,OverflowError) as exc:
            self.log_error('Error operativo %s',str(exc))
            return self.respond({'error':'Error interno al guardar datos'},500)


def serve():
    print(f'Predice-IA MVP local: http://127.0.0.1:{PORT}')
    print('No expongas este servidor a Internet: no incluye autenticación SaaS.')
    ThreadingHTTPServer(('127.0.0.1',PORT),API).serve_forever()

if __name__=='__main__':serve()
