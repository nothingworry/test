from http.server import BaseHTTPRequestHandler
import json
import os
from datetime import datetime
import uuid

# Simple in-memory storage (you'll want to replace this with a real database like MongoDB, PostgreSQL, or Vercel KV)
SCRIPTS_STORAGE = {}
STATS_STORAGE = {
    "total_scripts": 0,
    "total_requests": 0
}

API_KEY = os.environ.get('API_KEY', 'sk_live_9f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a1f0e9d8c7b6a5f4e3d2c1b0a')

def verify_api_key(key):
    return key == API_KEY

class handler(BaseHTTPRequestHandler):
    
    def send_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-API-Key')
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()
    
    def do_GET(self):
        if self.path == '/' or self.path == '/index':
            self.serve_html()
        elif self.path.startswith('/raw/'):
            self.serve_raw_script()
        else:
            self.send_error(404)
    
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else '{}'
        
        try:
            data = json.loads(body) if body else {}
        except:
            data = {}
        
        if self.path == '/api/verify':
            self.verify_key(data)
        elif self.path == '/api/upload':
            self.upload_script(data)
        elif self.path == '/api/scripts':
            self.list_scripts()
        else:
            self.send_error(404)
    
    def do_DELETE(self):
        if self.path.startswith('/api/delete/'):
            self.delete_script()
        else:
            self.send_error(404)
    
    def serve_html(self):
        html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LuaArmor Clone - Script Hosting</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        :root {
            --primary: #667eea; --primary-dark: #5568d3; --secondary: #764ba2;
            --success: #48bb78; --danger: #f56565; --dark: #1a202c;
            --light: #f7fafc; --border: #e2e8f0; --text: #2d3748;
            --text-light: #718096; --shadow: rgba(0, 0, 0, 0.1);
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            color: var(--text); line-height: 1.6; min-height: 100vh;
        }
        .screen { display: none; }
        .screen.active { display: block; }
        .container { min-height: 100vh; display: flex; justify-content: center; align-items: center; padding: 20px; }
        .login-box {
            background: white; border-radius: 20px; padding: 40px; max-width: 450px;
            width: 100%; box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            animation: slideUp 0.5s ease;
        }
        @keyframes slideUp { from { opacity: 0; transform: translateY(30px); } to { opacity: 1; transform: translateY(0); } }
        .logo { text-align: center; margin-bottom: 40px; }
        .logo-icon { font-size: 64px; margin-bottom: 15px; }
        .logo h1 {
            font-size: 32px; font-weight: 700;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            background-clip: text; margin-bottom: 5px;
        }
        .logo p { color: var(--text-light); font-size: 14px; }
        .input-group { margin-bottom: 20px; }
        label { display: block; color: var(--text); font-weight: 600; margin-bottom: 8px; font-size: 14px; }
        input[type="text"], input[type="password"], textarea {
            width: 100%; padding: 12px 16px; border: 2px solid var(--border);
            border-radius: 10px; font-size: 14px; transition: all 0.3s; font-family: inherit;
        }
        input:focus, textarea:focus {
            outline: none; border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        textarea { resize: vertical; min-height: 150px; font-family: 'Courier New', monospace; }
        .btn {
            padding: 12px 24px; border: none; border-radius: 10px; font-size: 14px;
            font-weight: 600; cursor: pointer; transition: all 0.3s;
            display: inline-flex; align-items: center; justify-content: center; gap: 8px;
        }
        .btn-primary {
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            color: white; width: 100%;
        }
        .btn-primary:hover { transform: translateY(-2px); box-shadow: 0 10px 25px rgba(102, 126, 234, 0.4); }
        .btn-secondary { background: var(--light); color: var(--text); }
        .btn-secondary:hover { background: var(--border); }
        .btn-small { padding: 8px 16px; font-size: 12px; }
        .btn-full { width: 100%; }
        .btn-danger { background: var(--danger); color: white; }
        .btn-danger:hover { background: #e53e3e; }
        .info-box {
            background: #f0f4ff; border: 2px solid #d0dbff;
            border-radius: 10px; padding: 15px; margin-top: 20px;
        }
        .info-box p { font-size: 12px; color: var(--text); margin-bottom: 8px; font-weight: 600; }
        .info-box code {
            display: block; background: white; padding: 10px; border-radius: 6px;
            font-size: 11px; color: var(--primary); word-break: break-all;
            font-family: 'Courier New', monospace;
        }
        .error-message {
            background: #fff5f5; color: var(--danger); padding: 12px;
            border-radius: 8px; margin-bottom: 20px; font-size: 14px;
            display: none; border-left: 4px solid var(--danger);
        }
        .error-message.show { display: block; animation: shake 0.5s; }
        @keyframes shake {
            0%, 100% { transform: translateX(0); }
            25% { transform: translateX(-10px); }
            75% { transform: translateX(10px); }
        }
        .navbar {
            background: white; box-shadow: 0 2px 10px var(--shadow);
            position: sticky; top: 0; z-index: 100;
        }
        .nav-content {
            max-width: 1200px; margin: 0 auto; padding: 15px 20px;
            display: flex; justify-content: space-between; align-items: center;
        }
        .nav-brand {
            display: flex; align-items: center; gap: 10px;
            font-size: 20px; font-weight: 700;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .logo-icon-small { font-size: 24px; }
        .dashboard-container { max-width: 1200px; margin: 0 auto; padding: 40px 20px; }
        .dashboard-header { margin-bottom: 30px; }
        .dashboard-header h1 { font-size: 36px; color: white; margin-bottom: 5px; }
        .dashboard-header p { color: rgba(255, 255, 255, 0.8); }
        .stats-grid {
            display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px; margin-bottom: 30px;
        }
        .stat-card {
            background: white; border-radius: 15px; padding: 25px;
            display: flex; align-items: center; gap: 20px;
            box-shadow: 0 4px 15px var(--shadow); transition: transform 0.3s;
        }
        .stat-card:hover { transform: translateY(-5px); }
        .stat-icon {
            font-size: 40px;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .stat-content h3 { font-size: 28px; color: var(--text); margin-bottom: 5px; }
        .stat-content p { font-size: 14px; color: var(--text-light); }
        .card {
            background: white; border-radius: 15px;
            box-shadow: 0 4px 15px var(--shadow); margin-bottom: 30px; overflow: hidden;
        }
        .card-header {
            padding: 20px 25px; border-bottom: 1px solid var(--border);
            display: flex; justify-content: space-between; align-items: center;
        }
        .card-header h2 { font-size: 20px; color: var(--text); }
        .card-body { padding: 25px; }
        .scripts-list { display: flex; flex-direction: column; gap: 15px; }
        .script-item {
            background: var(--light); border: 2px solid var(--border);
            border-radius: 12px; padding: 20px; transition: all 0.3s;
        }
        .script-item:hover {
            border-color: var(--primary);
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.1);
        }
        .script-header {
            display: flex; justify-content: space-between;
            align-items: flex-start; margin-bottom: 15px;
        }
        .script-info h3 { font-size: 18px; color: var(--text); margin-bottom: 5px; }
        .script-meta { font-size: 12px; color: var(--text-light); }
        .script-actions { display: flex; gap: 10px; }
        .script-stats {
            display: flex; gap: 20px; margin-bottom: 15px;
            font-size: 13px; color: var(--text-light);
        }
        .script-url {
            background: white; border: 1px solid var(--border);
            border-radius: 8px; padding: 12px;
            font-family: 'Courier New', monospace; font-size: 12px;
            color: var(--primary); word-break: break-all; margin-bottom: 10px;
        }
        .empty-state { text-align: center; padding: 40px; color: var(--text-light); }
        .modal {
            display: none; position: fixed; top: 0; left: 0;
            width: 100%; height: 100%; background: rgba(0, 0, 0, 0.7);
            z-index: 1000; align-items: center; justify-content: center;
        }
        .modal.show { display: flex; animation: fadeIn 0.3s; }
        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
        .modal-content {
            background: white; border-radius: 20px; max-width: 600px;
            width: 90%; max-height: 90vh; overflow-y: auto; animation: slideUp 0.3s;
        }
        .modal-header { padding: 25px; border-bottom: 1px solid var(--border); }
        .modal-header h2 { font-size: 24px; color: var(--text); }
        .modal-body { padding: 25px; }
        .modal-footer {
            padding: 20px 25px; border-top: 1px solid var(--border);
            display: flex; justify-content: flex-end;
        }
        .code-box {
            background: var(--light); border: 2px solid var(--border);
            border-radius: 10px; padding: 15px; margin-bottom: 15px;
        }
        .code-box label {
            display: block; font-size: 12px; font-weight: 600;
            color: var(--text); margin-bottom: 8px;
        }
        .code-box code {
            display: block; background: white; padding: 12px;
            border-radius: 6px; font-size: 12px; color: var(--primary);
            word-break: break-all; font-family: 'Courier New', monospace;
            margin-bottom: 10px;
        }
        @media (max-width: 768px) {
            .stats-grid { grid-template-columns: 1fr; }
            .script-header { flex-direction: column; gap: 15px; }
            .script-actions { width: 100%; }
            .script-actions button { flex: 1; }
        }
    </style>
</head>
<body>
    <div id="loginScreen" class="screen active">
        <div class="container">
            <div class="login-box">
                <div class="logo">
                    <div class="logo-icon">🔐</div>
                    <h1>LuaArmor</h1>
                    <p>Secure Luau Script Hosting</p>
                </div>
                <div id="loginError" class="error-message"></div>
                <div class="input-group">
                    <label for="apiKeyInput">API Key</label>
                    <input type="password" id="apiKeyInput" placeholder="Enter your API key...">
                </div>
                <button class="btn btn-primary" onclick="login()">Access Dashboard</button>
                <div class="info-box">
                    <p>🔑 Default API Key:</p>
                    <code>sk_live_9f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a1f0e9d8c7b6a5f4e3d2c1b0a</code>
                </div>
            </div>
        </div>
    </div>
    <div id="dashboardScreen" class="screen">
        <nav class="navbar">
            <div class="nav-content">
                <div class="nav-brand">
                    <div class="logo-icon-small">🔐</div>
                    <span>LuaArmor</span>
                </div>
                <div class="nav-actions">
                    <button class="btn btn-secondary" onclick="logout()">Logout</button>
                </div>
            </div>
        </nav>
        <div class="dashboard-container">
            <div class="dashboard-header">
                <h1>Dashboard</h1>
                <p>Manage your Luau scripts</p>
            </div>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-icon">📝</div>
                    <div class="stat-content">
                        <h3 id="totalScripts">0</h3>
                        <p>Total Scripts</p>
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon">📊</div>
                    <div class="stat-content">
                        <h3 id="totalRequests">0</h3>
                        <p>Total Requests</p>
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon">✅</div>
                    <div class="stat-content">
                        <h3>Active</h3>
                        <p>API Status</p>
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon">🔑</div>
                    <div class="stat-content">
                        <h3>Premium</h3>
                        <p>Account Type</p>
                    </div>
                </div>
            </div>
            <div class="card">
                <div class="card-header">
                    <h2>📤 Upload New Script</h2>
                </div>
                <div class="card-body">
                    <div class="input-group">
                        <label for="scriptName">Script Name</label>
                        <input type="text" id="scriptName" placeholder="My Awesome Script">
                    </div>
                    <div class="input-group">
                        <label for="scriptCode">Luau Code</label>
                        <textarea id="scriptCode" placeholder="-- Your Luau code here
print('Hello from LuaArmor!')" rows="10"></textarea>
                    </div>
                    <button class="btn btn-primary btn-full" onclick="uploadScript()">🚀 Upload Script</button>
                </div>
            </div>
            <div class="card">
                <div class="card-header">
                    <h2>📚 Your Scripts</h2>
                    <button class="btn btn-secondary btn-small" onclick="loadScripts()">🔄 Refresh</button>
                </div>
                <div class="card-body">
                    <div id="scriptsList" class="scripts-list">
                        <div class="empty-state">
                            <p>No scripts uploaded yet. Upload your first script above!</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <div id="successModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2>✅ Script Uploaded!</h2>
            </div>
            <div class="modal-body">
                <p>Your script has been uploaded successfully!</p>
                <div class="code-box">
                    <label>Loadstring:</label>
                    <code id="loadstringCode"></code>
                    <button class="btn btn-secondary btn-small" onclick="copyLoadstring()">📋 Copy</button>
                </div>
                <div class="code-box">
                    <label>Direct URL:</label>
                    <code id="directUrl"></code>
                    <button class="btn btn-secondary btn-small" onclick="copyUrl()">📋 Copy</button>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-primary" onclick="closeModal()">Done</button>
            </div>
        </div>
    </div>
    <script>
        const API_BASE = '';
        let currentApiKey = null;

        document.addEventListener('DOMContentLoaded', () => {
            const savedKey = sessionStorage.getItem('apiKey');
            if (savedKey) {
                currentApiKey = savedKey;
                showDashboard();
            }
            document.getElementById('apiKeyInput').addEventListener('keypress', (e) => {
                if (e.key === 'Enter') login();
            });
        });

        async function login() {
            const apiKeyInput = document.getElementById('apiKeyInput').value.trim();
            const errorMsg = document.getElementById('loginError');
            if (!apiKeyInput) {
                showError(errorMsg, 'Please enter an API key');
                return;
            }
            try {
                const response = await fetch(API_BASE + '/api/verify', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ api_key: apiKeyInput })
                });
                const data = await response.json();
                if (data.success) {
                    currentApiKey = apiKeyInput;
                    sessionStorage.setItem('apiKey', apiKeyInput);
                    document.getElementById('totalScripts').textContent = data.stats.total_scripts;
                    document.getElementById('totalRequests').textContent = data.stats.total_requests;
                    showDashboard();
                } else {
                    showError(errorMsg, 'Invalid API key. Please try again.');
                }
            } catch (error) {
                showError(errorMsg, 'Connection error. Please try again.');
            }
        }

        function logout() {
            sessionStorage.removeItem('apiKey');
            currentApiKey = null;
            document.getElementById('apiKeyInput').value = '';
            document.getElementById('scriptName').value = '';
            document.getElementById('scriptCode').value = '';
            showLogin();
        }

        function showDashboard() {
            document.getElementById('loginScreen').classList.remove('active');
            document.getElementById('dashboardScreen').classList.add('active');
            loadScripts();
        }

        function showLogin() {
            document.getElementById('dashboardScreen').classList.remove('active');
            document.getElementById('loginScreen').classList.add('active');
        }

        async function uploadScript() {
            const scriptName = document.getElementById('scriptName').value.trim() || 'Untitled Script';
            const scriptCode = document.getElementById('scriptCode').value.trim();
            if (!scriptCode) {
                alert('Please enter some code to upload!');
                return;
            }
            try {
                const response = await fetch(API_BASE + '/api/upload', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-API-Key': currentApiKey
                    },
                    body: JSON.stringify({ name: scriptName, code: scriptCode })
                });
                const data = await response.json();
                if (data.success) {
                    document.getElementById('scriptName').value = '';
                    document.getElementById('scriptCode').value = '';
                    showSuccessModal(data.loadstring, data.url);
                    loadScripts();
                } else {
                    alert('Upload failed: ' + data.message);
                }
            } catch (error) {
                alert('Upload error. Please try again.');
            }
        }

        async function loadScripts() {
            const scriptsList = document.getElementById('scriptsList');
            try {
                const response = await fetch(API_BASE + '/api/scripts', {
                    method: 'POST',
                    headers: { 'X-API-Key': currentApiKey }
                });
                const data = await response.json();
                if (data.success) {
                    document.getElementById('totalScripts').textContent = data.scripts.length;
                    const totalReqs = data.scripts.reduce((sum, script) => sum + script.requests, 0);
                    document.getElementById('totalRequests').textContent = totalReqs;
                    if (data.scripts.length === 0) {
                        scriptsList.innerHTML = '<div class="empty-state"><p>No scripts uploaded yet. Upload your first script above!</p></div>';
                    } else {
                        scriptsList.innerHTML = data.scripts.map(script => createScriptCard(script)).join('');
                    }
                }
            } catch (error) {
                scriptsList.innerHTML = '<div class="empty-state"><p>Error loading scripts. Please refresh the page.</p></div>';
            }
        }

        function createScriptCard(script) {
            const date = new Date(script.created).toLocaleString();
            const loadstring = `loadstring(game:HttpGet("${script.url}"))()`;
            return `
                <div class="script-item">
                    <div class="script-header">
                        <div class="script-info">
                            <h3>📝 ${escapeHtml(script.name)}</h3>
                            <div class="script-meta">ID: ${script.id} • Created: ${date}</div>
                        </div>
                        <div class="script-actions">
                            <button class="btn btn-secondary btn-small" onclick="copyScriptUrl('${script.url}')">📋 Copy URL</button>
                            <button class="btn btn-danger btn-small" onclick="deleteScript('${script.id}', '${escapeHtml(script.name)}')">🗑️ Delete</button>
                        </div>
                    </div>
                    <div class="script-stats">
                        <span>📊 ${script.requests} requests</span>
                        <span>📦 ${formatBytes(script.size)}</span>
                    </div>
                    <div class="script-url">${escapeHtml(loadstring)}</div>
                    <button class="btn btn-secondary btn-small" onclick="copyLoadstringForScript('${escapeHtml(loadstring)}')">⚡ Copy Loadstring</button>
                </div>
            `;
        }

        async function deleteScript(scriptId, scriptName) {
            if (!confirm(`Are you sure you want to delete "${scriptName}"?`)) return;
            try {
                const response = await fetch(API_BASE + '/api/delete/' + scriptId, {
                    method: 'DELETE',
                    headers: { 'X-API-Key': currentApiKey }
                });
                const data = await response.json();
                if (data.success) loadScripts();
                else alert('Delete failed: ' + data.message);
            } catch (error) {
                alert('Delete error. Please try again.');
            }
        }

        function showSuccessModal(loadstring, url) {
            document.getElementById('loadstringCode').textContent = loadstring;
            document.getElementById('directUrl').textContent = url;
            document.getElementById('successModal').classList.add('show');
        }

        function closeModal() {
            document.getElementById('successModal').classList.remove('show');
        }

        function copyLoadstring() {
            copyToClipboard(document.getElementById('loadstringCode').textContent);
        }

        function copyUrl() {
            copyToClipboard(document.getElementById('directUrl').textContent);
        }

        function copyScriptUrl(url) {
            copyToClipboard(url);
        }

        function copyLoadstringForScript(loadstring) {
            copyToClipboard(loadstring);
        }

        function copyToClipboard(text) {
            navigator.clipboard.writeText(text).then(() => {
                const originalBtn = event.target;
                const originalText = originalBtn.innerHTML;
                originalBtn.innerHTML = '✓ Copied!';
                originalBtn.style.background = '#48bb78';
                originalBtn.style.color = 'white';
                setTimeout(() => {
                    originalBtn.innerHTML = originalText;
                    originalBtn.style.background = '';
                    originalBtn.style.color = '';
                }, 2000);
            });
        }

        function showError(element, message) {
            element.textContent = message;
            element.classList.add('show');
            setTimeout(() => element.classList.remove('show'), 3000);
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        function formatBytes(bytes) {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
        }

        window.onclick = function(event) {
            const modal = document.getElementById('successModal');
            if (event.target === modal) closeModal();
        }
    </script>
</body>
</html>"""
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(html_content.encode())
    
    def serve_raw_script(self):
        script_id = self.path.split('/')[-1]
        
        if script_id in SCRIPTS_STORAGE:
            script_data = SCRIPTS_STORAGE[script_id]
            script_data['requests'] = script_data.get('requests', 0) + 1
            STATS_STORAGE['total_requests'] += 1
            
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(script_data['code'].encode('utf-8'))
        else:
            self.send_response(404)
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(b'Script not found')
    
    def verify_key(self, data):
        api_key = data.get('api_key', '')
        
        if verify_api_key(api_key):
            response = {
                "success": True,
                "message": "API key verified",
                "stats": {
                    "total_scripts": len(SCRIPTS_STORAGE),
                    "total_requests": STATS_STORAGE['total_requests']
                }
            }
            self.send_json_response(200, response)
        else:
            self.send_json_response(401, {"success": False, "message": "Invalid API key"})
    
    def upload_script(self, data):
        api_key = self.headers.get('X-API-Key', '')
        
        if not verify_api_key(api_key):
            self.send_json_response(401, {"success": False, "message": "Invalid API key"})
            return
        
        script_name = data.get('name', 'Untitled')
        script_code = data.get('code', '')
        
        if not script_code:
            self.send_json_response(400, {"success": False, "message": "No code provided"})
            return
        
        script_id = str(uuid.uuid4())[:8]
        
        SCRIPTS_STORAGE[script_id] = {
            "name": script_name,
            "code": script_code,
            "created": datetime.now().isoformat(),
            "requests": 0,
            "size": len(script_code)
        }
        
        STATS_STORAGE['total_scripts'] = len(SCRIPTS_STORAGE)
        
        # Get the host from the request
        host = self.headers.get('Host', 'localhost')
        script_url = f"https://{host}/raw/{script_id}"
        
        response = {
            "success": True,
            "message": "Script uploaded successfully",
            "script_id": script_id,
            "url": script_url,
            "loadstring": f'loadstring(game:HttpGet("{script_url}"))()'
        }
        
        self.send_json_response(200, response)
    
    def list_scripts(self):
        api_key = self.headers.get('X-API-Key', '')
        
        if not verify_api_key(api_key):
            self.send_json_response(401, {"success": False, "message": "Invalid API key"})
            return
        
        host = self.headers.get('Host', 'localhost')
        scripts_list = []
        
        for script_id, script_data in SCRIPTS_STORAGE.items():
            scripts_list.append({
                "id": script_id,
                "name": script_data['name'],
                "created": script_data['created'],
                "requests": script_data.get('requests', 0),
                "size": script_data.get('size', 0),
                "url": f"https://{host}/raw/{script_id}"
            })
        
        scripts_list.sort(key=lambda x: x['created'], reverse=True)
        
        self.send_json_response(200, {
            "success": True,
            "scripts": scripts_list
        })
    
    def delete_script(self):
        api_key = self.headers.get('X-API-Key', '')
        
        if not verify_api_key(api_key):
            self.send_json_response(401, {"success": False, "message": "Invalid API key"})
            return
        
        script_id = self.path.split('/')[-1]
        
        if script_id in SCRIPTS_STORAGE:
            del SCRIPTS_STORAGE[script_id]
            STATS_STORAGE['total_scripts'] = len(SCRIPTS_STORAGE)
            self.send_json_response(200, {"success": True, "message": "Script deleted"})
        else:
            self.send_json_response(404, {"success": False, "message": "Script not found"})
    
    def send_json_response(self, status_code, data):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
