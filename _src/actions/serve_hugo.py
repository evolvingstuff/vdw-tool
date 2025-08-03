import os
import http.server
import socketserver
import threading
import time
import subprocess
import signal

def kill_process_on_port(port):
    """Kill any process using the specified port"""
    try:
        # Find process using the port
        result = subprocess.run(['lsof', '-ti', f':{port}'], 
                              capture_output=True, text=True, check=False)
        
        if result.returncode == 0 and result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                if pid:
                    try:
                        print(f"🔄 Killing process {pid} using port {port}")
                        os.kill(int(pid), signal.SIGTERM)
                        time.sleep(0.5)  # Give it a moment to clean up
                    except (ProcessLookupError, ValueError):
                        pass  # Process already dead or invalid PID
            return True
    except FileNotFoundError:
        # lsof not available, try alternative approach with netstat
        try:
            result = subprocess.run(['netstat', '-tulpn'], 
                                  capture_output=True, text=True, check=False)
            for line in result.stdout.split('\n'):
                if f':{port}' in line and 'LISTEN' in line:
                    print(f"🔄 Port {port} appears to be in use, attempting to continue...")
                    return False
        except FileNotFoundError:
            pass
    return False

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
    
    # Kill any existing process on the port
    kill_process_on_port(port)
    
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