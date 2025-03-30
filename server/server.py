#!/usr/bin/env python3
"""
Simple HTTP server for serving Blender Web Preview files.
Usage: python server.py [port] [directory]
"""

import sys
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
import socketserver

def run_server(port, directory):
    """Run a simple HTTP server on the specified port and directory"""
    
    # Change to the specified directory
    os.chdir(directory)
    
    # Create a request handler that logs minimally
    class QuietHandler(SimpleHTTPRequestHandler):
        def log_message(self, format, *args):
            # Minimal logging to keep console clean
            print(f"HTTP: {format % args}")
            
        def end_headers(self):
            # Add CORS headers to allow loading from any origin
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET')
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
            super().end_headers()
    
    # Create a threaded HTTP server
    class ThreadedHTTPServer(socketserver.ThreadingMixIn, HTTPServer):
        """Handle requests in a separate thread."""
        daemon_threads = True
    
    # Create and start the server
    server = ThreadedHTTPServer(("", port), QuietHandler)
    print(f"Server started at http://localhost:{port}")
    print(f"Serving files from: {directory}")
    print("Press Ctrl+C to stop")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Server stopped.")
    finally:
        server.server_close()

if __name__ == "__main__":
    # Get command line arguments
    if len(sys.argv) < 3:
        print("Usage: python server.py [port] [directory]")
        sys.exit(1)
    
    port = int(sys.argv[1])
    directory = sys.argv[2]
    
    # Run the server
    run_server(port, directory)