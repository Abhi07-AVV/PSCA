# server.py

import os
import json
import shutil
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import tempfile
import threading
import time
from proposal_checker import analyze_proposals

# Configuration
DATASET_FOLDER = "Sample Poroposal"
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

class ProposalCheckerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/' or parsed_path.path == '/index.html':
            self.serve_file('index.html', 'text/html')
        elif parsed_path.path == '/styles.css':
            self.serve_file('styles.css', 'text/css')
        elif parsed_path.path == '/script.js':
            self.serve_file('script.js', 'application/javascript')
        elif parsed_path.path == '/api/dataset':
            self.serve_dataset_info()
        else:
            self.send_error(404, "File not found")
    
    def do_POST(self):
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/upload':
            self.handle_file_upload()
        elif parsed_path.path == '/api/analyze':
            self.analyze_proposal()
        else:
            self.send_error(404, "Endpoint not found")
    
    def serve_file(self, filename, content_type):
        try:
            with open(filename, 'rb') as file:
                content = file.read()
            
            self.send_response(200)
            self.send_header('Content-type', content_type)
            self.end_headers()
            self.wfile.write(content)
        except FileNotFoundError:
            self.send_error(404, "File not found")
    
    def serve_dataset_info(self):
        if not os.path.exists(DATASET_FOLDER):
            dataset_files = []
        else:
            dataset_files = []
            for root, dirs, files in os.walk(DATASET_FOLDER):
                for file in files:
                    if file.lower().endswith('.pdf'):
                        dataset_files.append(os.path.join(root, file))
        
        response = {
            'count': len(dataset_files),
            'files': [os.path.relpath(f, DATASET_FOLDER) for f in dataset_files]
        }
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())
    
    def handle_file_upload(self):
        # Get the content length
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        # Get the filename from the headers
        content_type = self.headers['Content-Type']
        if 'boundary' in content_type:
            # Parse multipart form data
            boundary = content_type.split('boundary=')[1]
            parts = post_data.split(f'--{boundary}'.encode())
            
            for part in parts:
                if b'filename="' in part:
                    # Extract filename
                    filename_start = part.find(b'filename="') + len(b'filename="')
                    filename_end = part.find(b'"', filename_start)
                    filename = part[filename_start:filename_end].decode('utf-8')
                    
                    # Extract file data (skip headers)
                    data_start = part.find(b'\r\n\r\n') + 4
                    file_data = part[data_start:]
                    
                    # Remove trailing boundary
                    if file_data.endswith(f'--{boundary}--\r\n'.encode()):
                        file_data = file_data[:-len(f'--{boundary}--\r\n'.encode())]
                    elif file_data.endswith(f'--{boundary}--'.encode()):
                        file_data = file_data[:-len(f'--{boundary}--'.encode())]
                    elif file_data.endswith(f'--{boundary}'.encode()):
                        file_data = file_data[:-len(f'--{boundary}'.encode())]
                    
                    # Save to uploads folder
                    file_path = os.path.join(UPLOAD_FOLDER, "uploaded_proposal.pdf")
                    with open(file_path, 'wb') as f:
                        f.write(file_data)
                    
                    response = {
                        'success': True,
                        'filename': filename,
                        'size': len(file_data)
                    }
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(response).encode())
                    return
        
        self.send_error(400, "No file uploaded")
    
    def analyze_proposal(self):
        try:
            # Copy the uploaded file to the expected location for proposal_checker
            uploaded_path = os.path.join(UPLOAD_FOLDER, "uploaded_proposal.pdf")
            target_path = "your_uploaded_proposal.pdf"
            
            if os.path.exists(uploaded_path):
                shutil.copy2(uploaded_path, target_path)
            else:
                raise FileNotFoundError("Uploaded file not found")
            
            # Check if the PDF file has content before analysis
            if os.path.getsize(target_path) == 0:
                raise ValueError("Uploaded PDF file is empty")
            
            # Run the actual proposal checker analysis
            result = self.run_proposal_analysis()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
        except FileNotFoundError as e:
            error_msg = f"File error: {str(e)}"
            print(f"Error during analysis: {error_msg}")
            self.send_error(404, error_msg)
        except ValueError as e:
            error_msg = f"Invalid file: {str(e)}"
            print(f"Error during analysis: {error_msg}")
            self.send_error(400, error_msg)
        except Exception as e:
            error_msg = f"Analysis failed: {str(e)}"
            print(f"Error during analysis: {error_msg}")
            # Send a proper JSON error response instead of HTML
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_response = {
                'error': 'Analysis failed',
                'message': str(e)
            }
            self.wfile.write(json.dumps(error_response).encode())

    def run_proposal_analysis(self):
        """Run the actual proposal analysis"""
        try:
            # Import and run the proposal checker
            import proposal_checker
            
            # Run the analysis and get results
            result = proposal_checker.analyze("your_uploaded_proposal.pdf")
            
            return result
        except Exception as e:
            print(f"Error in analysis: {e}")
            raise e

def start_server():
    # Start the server
    server_address = ('', 8000)
    httpd = HTTPServer(server_address, ProposalCheckerHandler)
    print("Starting server on http://localhost:8000")
    print("Press Ctrl+C to stop the server")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")

if __name__ == "__main__":
    start_server()