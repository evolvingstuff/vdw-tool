import os
import http.server
import socketserver
import threading
import time

def serve_hugo_site(port=1313):
    """Serve the built Hugo site using Python's built-in HTTP server"""
    
    # Check if hugo_output directory exists
    if not os.path.exists('hugo_output'):
        print("❌ No hugo_output/ directory found. Build the Hugo site first.")
        return False
    
    # Check if there's an index.html file
    if not os.path.exists('hugo_output/index.html'):
        print("❌ No index.html found in hugo_output/. The site may not be built properly.")
        return False
    
    try:
        # Change to the hugo_output directory
        original_dir = os.getcwd()
        os.chdir('hugo_output')
        
        print(f"🌐 Starting HTTP server on localhost:{port}")
        print(f"📁 Serving files from: {os.getcwd()}")
        print(f"🔗 Open http://localhost:{port} in your browser")
        print("⏹️  Press Ctrl+C to stop the server")
        
        # Create HTTP server
        handler = http.server.SimpleHTTPRequestHandler
        with socketserver.TCPServer(("", port), handler) as httpd:
            print(f"✅ Server running at http://localhost:{port}")
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print("\n🛑 Server stopped by user")
                
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"❌ Port {port} is already in use. Try a different port or stop the existing server.")
        else:
            print(f"❌ Error starting server: {e}")
        return False
    except Exception as e:
        print(f"❌ Error serving Hugo site: {e}")
        return False
    finally:
        # Change back to original directory
        os.chdir(original_dir)
    
    return True

if __name__ == '__main__':
    serve_hugo_site()