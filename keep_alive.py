from flask import Flask
from threading import Thread

app = Flask(__name__)

@app.route('/')
def home():
    return """
    <!DOCTYPE html>
    <html>
        <head>
            <title>Marvel Bot Status</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                * {
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                    padding: 20px;
                }
                .container {
                    text-align: center;
                    padding: 60px 40px;
                    background: rgba(0, 0, 0, 0.3);
                    border-radius: 20px;
                    box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
                    backdrop-filter: blur(4px);
                    border: 1px solid rgba(255, 255, 255, 0.18);
                    max-width: 600px;
                    width: 100%;
                }
                h1 {
                    font-size: 48px;
                    margin-bottom: 20px;
                    text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
                }
                .status-container {
                    margin: 30px 0;
                }
                .status {
                    display: inline-flex;
                    align-items: center;
                    gap: 10px;
                    font-size: 24px;
                    padding: 15px 30px;
                    background: rgba(0, 255, 0, 0.2);
                    border-radius: 50px;
                    border: 2px solid #00ff00;
                }
                .status-dot {
                    width: 20px;
                    height: 20px;
                    background-color: #00ff00;
                    border-radius: 50%;
                    animation: pulse 2s infinite;
                }
                @keyframes pulse {
                    0%, 100% {
                        opacity: 1;
                        transform: scale(1);
                    }
                    50% {
                        opacity: 0.5;
                        transform: scale(1.1);
                    }
                }
                .info {
                    font-size: 18px;
                    margin-top: 30px;
                    line-height: 1.8;
                }
                .info-box {
                    background: rgba(255, 255, 255, 0.1);
                    padding: 20px;
                    border-radius: 10px;
                    margin-top: 20px;
                }
                .footer {
                    margin-top: 30px;
                    font-size: 14px;
                    opacity: 0.8;
                }
                a {
                    color: #00ff00;
                    text-decoration: none;
                }
                a:hover {
                    text-decoration: underline;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🤖 Marvel Bot</h1>
                <div class="status-container">
                    <div class="status">
                        <span class="status-dot"></span>
                        <span>Online</span>
                    </div>
                </div>
                <div class="info">
                    <p><strong>Platform:</strong> GitHub Actions</p>
                    <div class="info-box">
                        <p><strong>📊 Features:</strong></p>
                        <p>✅ نظام تذاكر متكامل</p>
                        <p>✅ إدارة حسابات Level 15</p>
                        <p>✅ إحصائيات تلقائية</p>
                        <p>✅ حفظ البيانات التلقائي</p>
                    </div>
                    <div class="info-box">
                        <p><strong>⚙️ System Info:</strong></p>
                        <p>🔄 Auto-restart every ~6 hours</p>
                        <p>💾 Data saved automatically</p>
                        <p>🔒 Secure & reliable</p>
                    </div>
                </div>
                <div class="footer">
                    <p>Marvel Discord Bot © 2024</p>
                    <p>Made with ❤️ for Discord</p>
                </div>
            </div>
        </body>
    </html>
    """

@app.route('/health')
def health():
    return {
        "status": "healthy",
        "message": "Bot is running",
        "platform": "GitHub Actions"
    }, 200

@app.route('/ping')
def ping():
    return {"response": "pong"}, 200

def run():
    """تشغيل Flask server"""
    app.run(host='0.0.0.0', port=8080, debug=False)

def keep_alive():
    """Start Flask server in a separate thread"""
    t = Thread(target=run, daemon=True)
    t.start()
    print("✅ Keep-alive server started on http://0.0.0.0:8080")
