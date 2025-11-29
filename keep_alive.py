from flask import Flask
from threading import Thread

app = Flask(__name__)

@app.route('/')
def home():
    return """
    <html>
        <head>
            <title>Marvel Bot Status</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                }
                .container {
                    text-align: center;
                    padding: 40px;
                    background: rgba(0, 0, 0, 0.3);
                    border-radius: 20px;
                    box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
                }
                h1 { font-size: 48px; margin: 0; }
                p { font-size: 20px; margin-top: 20px; }
                .status {
                    display: inline-block;
                    width: 20px;
                    height: 20px;
                    background-color: #00ff00;
                    border-radius: 50%;
                    margin-right: 10px;
                    animation: pulse 2s infinite;
                }
                @keyframes pulse {
                    0%, 100% { opacity: 1; }
                    50% { opacity: 0.5; }
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🤖 Marvel Bot</h1>
                <p><span class="status"></span>Status: Online</p>
                <p>Bot is running on GitHub Actions</p>
            </div>
        </body>
    </html>
    """

@app.route('/health')
def health():
    return {"status": "healthy", "message": "Bot is running"}, 200

def run():
    app.run(host='0.0.0.0', port=8080, debug=False)

def keep_alive():
    """Start Flask server in a separate thread"""
    t = Thread(target=run, daemon=True)
    t.start()
    print("✅ Keep-alive server started on port 8080")