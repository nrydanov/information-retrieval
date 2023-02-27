from http.server import ThreadingHTTPServer, HTTPServer
from http.server import BaseHTTPRequestHandler
from handler import RequestHandler

def run(server_class=HTTPServer, handler_class=BaseHTTPRequestHandler):
  server_address = ('', 3000)
  httpd = server_class(server_address, handler_class)
  httpd.serve_forever()
  
  
run(ThreadingHTTPServer, RequestHandler)