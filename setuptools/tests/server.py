"""Basic http server for tests to simulate PyPI or custom indexes
"""

import os
import time
import threading

from setuptools.extern.six.moves import BaseHTTPServer, SimpleHTTPServer
from setuptools.extern.six.moves.urllib_parse import urljoin
from setuptools.extern.six.moves.urllib.request import pathname2url


class IndexServer(BaseHTTPServer.HTTPServer):
    """Basic single-threaded http server simulating a package index

    You can use this server in unittest like this::
        s = IndexServer()
        s.start()
        index_url = s.base_url() + 'mytestindex'
        # do some test requests to the index
        # The index files should be located in setuptools/tests/indexes
        s.stop()
    """

    def __init__(
            self, server_address=('', 0),
            RequestHandlerClass=SimpleHTTPServer.SimpleHTTPRequestHandler):
        BaseHTTPServer.HTTPServer.__init__(
            self, server_address, RequestHandlerClass)
        self._run = True

    def start(self):
        self.thread = threading.Thread(target=self.serve_forever)
        self.thread.start()

    def stop(self):
        "Stop the server"

        # Let the server finish the last request and wait for a new one.
        time.sleep(0.1)

        self.shutdown()
        self.thread.join()
        self.socket.close()

    def base_url(self):
        port = self.server_port
        return f'http://127.0.0.1:{port}/setuptools/tests/indexes/'


class RequestRecorder(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(self):
        requests = vars(self.server).setdefault('requests', [])
        requests.append(self)
        self.send_response(200, 'OK')


class MockServer(BaseHTTPServer.HTTPServer, threading.Thread):
    """
    A simple HTTP Server that records the requests made to it.
    """

    def __init__(
            self, server_address=('', 0),
            RequestHandlerClass=RequestRecorder):
        BaseHTTPServer.HTTPServer.__init__(
            self, server_address, RequestHandlerClass)
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.requests = []

    def run(self):
        self.serve_forever()

    @property
    def netloc(self):
        return f'localhost:{self.server_port}'

    @property
    def url(self):
        return f'http://{self.netloc}/'


def path_to_url(path, authority=None):
    """ Convert a path to a file: URL. """
    path = os.path.normpath(os.path.abspath(path))
    base = 'file:'
    if authority is not None:
        base += f'//{authority}'
    return urljoin(base, pathname2url(path))
