import pytest
from tests.support.s16 import probe

pytestmark=[pytest.mark.scripts,pytest.mark.integration]


def test_script_binding_and_real_no_cache_http(tmp_path):
    probe('''
import runpy,socketserver,threading,functools,urllib.request,http.server
from tests.support.imports import REPO_ROOT
server=Mock(); server.__enter__=Mock(return_value=server); server.__exit__=Mock(return_value=False)
with patch.object(socketserver,'TCPServer',return_value=server) as constructor:
    ns=runpy.run_path(str(REPO_ROOT/'browser/webserver.py'))
constructor.assert_called_once_with(('',8000),ns['NoCacheHTTPRequestHandler'])
server.serve_forever.assert_called_once_with()
Path('sample.txt').write_text('test body')
handler=functools.partial(ns['NoCacheHTTPRequestHandler'],directory=str(Path.cwd()))
with socketserver.TCPServer(('127.0.0.1',0),handler) as actual:
    thread=threading.Thread(target=actual.serve_forever); thread.start()
    try:
        with urllib.request.urlopen(f'http://127.0.0.1:{actual.server_address[1]}/sample.txt',timeout=5) as response:
            assert response.read()==b'test body'
            assert response.headers['Content-Type']=='text/plain'
            assert response.headers['Cache-Control']=='no-cache, no-store, must-revalidate'
            assert response.headers['Pragma']=='no-cache' and response.headers['Expires']=='0'
    finally: actual.shutdown(); thread.join(timeout=5)
assert not thread.is_alive()
''',tmp_path)
