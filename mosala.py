import json
import os
import tempfile
from datetime import datetime
from urllib.parse import urlparse
from flask import Flask, render_template_string, request, redirect, url_for, session, abort
from werkzeug.security import generate_password_hash, check_password_hash
from markupsafe import escape

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'CHANGE-THIS-SECRET-KEY-BEFORE-DEPLOYMENT')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, 'school_data.json')


def safe_html(value):
    """Escape user-managed text while retaining legacy <br> line breaks."""
    escaped = str(escape('' if value is None else value))
    return escaped.replace('&lt;br&gt;', '<br>').replace('&lt;br/&gt;', '<br>').replace('&lt;br /&gt;', '<br>')


def localized_value(item, field, default=''):
    """Return the English field when English is selected and available."""
    if request.cookies.get('ario-language') == 'en':
        english_value = item.get(field + '_en')
        if english_value not in (None, ''):
            return english_value
    return item.get(field, default)

# ==========================================
# مدیریت دیتای پویا (شامل کاربران)
# ==========================================
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                if 'sections' not in data: data['sections'] = {}
                for sec in ['home', 'staff', 'activities', 'news']:
                    if sec not in data['sections']: data['sections'][sec] = []
                if 'settings' not in data: data['settings'] = {}
                data['settings'].setdefault('home_title', 'جایی که درس، ایده و حال خوب کنار هم می‌نشینند.')
                data['settings'].setdefault('home_subtitle', 'ما یک مدرسه نیستیم؛ یک تیمیم. تیمی برای یادگیری و رشد.')
                data['settings'].setdefault('about_text', 'آریو مصلی‌نژاد، خانه یادگیری، دوستی و ساختن آینده است.')
                if 'users' not in data: 
                    data['users'] = {
                        "admin": {"password": "123", "role": "مدیر سایت (شما)"},
                        "modir": {"password": "123", "role": "مدیر مدرسه"}
                    }
                return data
            except: pass
    
    default_data = {
        "users": {
            "admin": {"password": "123", "role": "مدیر سایت (شما)"},
            "modir": {"password": "123", "role": "مدیر مدرسه"}
        },
        "settings": {
            "home_title": "جایی که درس، ایده و حال خوب کنار هم می‌نشینند.",
            "home_subtitle": "ما یک مدرسه نیستیم؛ یک تیمیم. تیمی از دانش‌آموزان کنجکاو، دبیرهای پایه‌کار و کادری که با عشق و تلاش، مدرسه را به جای بهتری برای رشد و شکوفایی تبدیل می‌کنند.",
            "about_text": "آریو مصلی‌نژاد فقط یک اسم روی سربرگ نیست. یک مدرسه دولتی پسرانه در ارومیه است که با مدیریت دلسوزانه آقای سلاطین و تلاش کادر مجرب، محیطی امن و پویا برای آینده‌سازان این مرز و بوم فراهم کرده است."
        },
        "sections": {
            "home": [
                {"title": "ما کی هستیم", "text": "مدرسه دولتی پسرانه در ارومیه", "icon": "fa-school"},
                {"title": "طراح سایت", "text": "محمد امین سعیدی و امیرعباس قاسمی", "icon": "fa-laptop-code"},
                {"title": "آیدی", "text": "آیدی ایتای سعیدی:@amin_Hr <br> آیدی ایتای قاسمی:@Amir_ghasemi1390 <br> آیدی روبیکای سعیدی:@AMINHANDALA <br> آیدی روبیکای قاسمی:@xode_Griffin", "icon": "fa-mobile-alt"},
                {"title": "روش ما", "text": "ترکیبی از آموزش منظم، فعالیت‌های دانش‌آموزی و فضایی دوستانه برای یادگیری بهتر", "icon": "fa-book-open"},
                {"title": "کتابخانه", "text": "فضایی آرام برای مطالعه، امانت کتاب و رشد اندیشه", "icon": "fa-book"}
            ],
            "staff": [
                {"title": "جناب آقای سلاطین", "text": "مدیر مدرسه", "icon": "fa-user-tie"},
                {"title": "جناب آقای الوانی", "text": "معاون آموزشی", "icon": "fa-user-graduate"}
            ],
            "activities": [
                {"title": "گروه هنری و تئاتر", "text": "اجرای نمایش‌های زیبا در مناسبت‌های مختلف.", "icon": "fa-theater-masks"},
                {"title": "نشریه دانش‌آموزی", "text": "قلم و ایده دانش‌آموزان در قالب نشریه.", "icon": "fa-newspaper"},
                {"title": "المپیاد ورزشی", "text": "رقابت سالم و پرشاط بین کلاس‌ها.", "icon": "fa-trophy"}
            ],
            "news": [
                {"title": "روز دانش‌آموز", "text": "روز دانش‌آموز، روز تجلیل از آینده‌سازان این مرز و بوم است.", "icon": "fa-birthday-cake"}
            ]
        }
    }
    save_data(default_data)
    return default_data

def save_data(data):
    """Persist site content on disk using an atomic replace to avoid partial files."""
    os.makedirs(BASE_DIR, exist_ok=True)
    fd, temp_path = tempfile.mkstemp(prefix='school_data_', suffix='.tmp', dir=BASE_DIR)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            f.flush()
            os.fsync(f.fileno())
        # Keep the previous valid data as a recovery copy.
        if os.path.exists(DATA_FILE):
            backup_path = DATA_FILE + '.bak'
            with open(DATA_FILE, 'rb') as src, open(backup_path, 'wb') as dst:
                dst.write(src.read())
                dst.flush()
                os.fsync(dst.fileno())
        os.replace(temp_path, DATA_FILE)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        # ==========================================
# قالب پایه (تم روشن + ریسپانسیو + افکت شیشه‌ای)
# ==========================================
BASE_TEMPLATE = """
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="theme-color" content="#080d18">
    <title>مدرسه آریو مصلی‌نژاد | {{ title }}</title>
    <link href="https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css" rel="stylesheet" type="text/css" />
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Vazirmatn', sans-serif; }
        
        /* نور آبی ملایم در پس‌زمینه همه صفحات */
        body { 
            background-color: #f4f7fc; 
            background-image: radial-gradient(circle at 50% 50%, #e0f2fe 0%, #f4f7fc 60%); 
            color: #333; 
            min-height: 100vh; 
        }
        
        /* هدر و منو */
        header { background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(10px); padding: 15px 50px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 10px rgba(0,0,0,0.03); position: sticky; top: 0; z-index: 1000; }
        .logo-container { display: flex; align-items: center; gap: 15px; }
        .logo-box { width: 40px; height: 40px; background: #3b82f6; border-radius: 8px; display: flex; justify-content: center; align-items: center; color: white; font-size: 1.5rem; font-weight: bold; }
        .logo-text { font-weight: 700; font-size: 1.1rem; color: #1e293b; }
        .logo-text span { display: block; font-size: 0.75rem; color: #94a3b8; font-weight: 400; margin-top: 2px; }
        
        nav { display: flex; gap: 5px; align-items: center; }
        nav a { text-decoration: none; color: #64748b; font-weight: 500; font-size: 0.9rem; padding: 8px 16px; border-radius: 8px; transition: all 0.3s; white-space: nowrap; }
        nav a:hover, nav a.active { background: #eff6ff; color: #1e293b; }
        
        .auth-btns { display: flex; gap: 10px; }
        .btn-outline { text-decoration: none; color: #3b82f6; border: 1px solid #3b82f6; padding: 8px 20px; border-radius: 8px; font-size: 0.9rem; font-weight: 600; transition: 0.3s; white-space: nowrap; }
        .btn-outline:hover { background: #eff6ff; }
        
        /* کانتینرها */
        .container { padding: 60px 50px; max-width: 1200px; margin: 0 auto; }
        .page-title { text-align: center; font-size: 2.2rem; color: #1e3a8a; margin-bottom: 25px; font-weight: 800; }
        
        /* کادر شیشه‌ای برای متن‌ها */
        .hero-card { 
            background: rgba(255, 255, 255, 0.7); 
            backdrop-filter: blur(10px); 
            border: 1px solid rgba(255, 255, 255, 0.5);
            padding: 30px 40px; 
            border-radius: 20px; 
            text-align: center; 
            color: #475569; 
            font-size: 1.1rem; 
            line-height: 1.8; 
            max-width: 900px;
            margin: 0 auto 50px auto; 
            box-shadow: 0 10px 30px rgba(0,0,0,0.03); 
        }
        
        /* کارت‌های اصلی */
        .grid-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 30px; justify-content: center; }
        .card { background: #ffffff; padding: 40px 30px; border-radius: 20px; text-align: center; box-shadow: 0 4px 20px rgba(0,0,0,0.03); transition: all 0.3s ease; border: 1px solid #f1f5f9; display: flex; flex-direction: column; align-items: center; justify-content: center; }
        .card:hover { transform: translateY(-5px); box-shadow: 0 10px 30px rgba(0,0,0,0.06); }
        .card i { font-size: 2.5rem; color: #3b82f6; margin-bottom: 25px; }
        .card h3 { font-size: 1.3rem; margin-bottom: 15px; color: #1e293b; font-weight: 700; }
        .card p { color: #64748b; line-height: 1.7; font-size: 0.95rem; }
        
        .btn-map { margin-top: 20px; background: #3b82f6; color: white; text-decoration: none; padding: 10px 20px; border-radius: 8px; font-size: 0.9rem; transition: 0.3s; display: inline-block; }
        
        /* پنل ادمین (شفاف شده تا نور پس‌زمینه از پشتش دیده بشه) */
        .admin-section { background: rgba(255, 255, 255, 0.85); backdrop-filter: blur(10px); padding: 30px; border-radius: 20px; margin-bottom: 30px; box-shadow: 0 4px 20px rgba(0,0,0,0.03); border: 1px solid #f1f5f9; }
        .admin-section h3 { color: #1e3a8a; margin-bottom: 20px; border-bottom: 2px solid #e0f2fe; padding-bottom: 10px; }
        .form-group { display: flex; flex-direction: column; gap: 10px; margin-bottom: 15px; }
        .form-group input, .form-group textarea, .form-group select { width: 100%; padding: 12px; border-radius: 8px; border: 1px solid #cbd5e1; font-family: inherit; outline: none; background: #fff; }
        
        .admin-form { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 20px; }
        .admin-list-item { display: flex; justify-content: space-between; align-items: center; background: #f8fafc; padding: 15px; border-radius: 12px; border: 1px solid #e2e8f0; margin-bottom: 10px; gap: 10px; }
        .btn-danger { background: #ef4444; color: white; text-decoration: none; padding: 8px 12px; border-radius: 8px; font-size: 0.8rem; transition: 0.3s; border: none; cursor: pointer; white-space: nowrap; }
        .btn-success { background: #10b981; color: white; text-decoration: none; padding: 10px 20px; border-radius: 8px; font-size: 0.9rem; transition: 0.3s; border: none; cursor: pointer; font-family: inherit; font-weight: bold; }
        .btn-warning { background: #f59e0b; color: white; text-decoration: none; padding: 8px 12px; border-radius: 8px; font-size: 0.8rem; transition: 0.3s; border: none; cursor: pointer; white-space: nowrap; }

        /* ========================================== */
        /* استایل مخصوص گوشی و تبلت (ریسپانسیو) */
        /* ========================================== */
        @media (max-width: 768px) {
            header { flex-direction: column; padding: 15px 20px; gap: 15px; }
            nav { flex-wrap: wrap; justify-content: center; width: 100%; }
            nav a { font-size: 0.8rem; padding: 6px 10px; }
            .auth-btns { width: 100%; justify-content: center; margin-top: 10px; }
            
            .container { padding: 30px 15px; }
            .page-title { font-size: 1.8rem !important; }
            
            .hero-card { padding: 20px; font-size: 0.95rem; margin-bottom: 30px; }
            
            .grid-cards { grid-template-columns: 1fr; gap: 20px; }
            .card { padding: 30px 20px; }
            
            .admin-section { padding: 20px 15px; }
            .admin-form { flex-direction: column; }
            .admin-form input, .admin-form select, .admin-form button { width: 100% !important; }
            .admin-list-item { flex-direction: column; align-items: flex-start; }
            .admin-list-item div:last-child { margin-top: 10px; align-self: flex-end; }
            .form-group input, .form-group textarea, .form-group select { font-size: 16px; }
        }

        /* ===== Modern international redesign ===== */
        :root { --ink:#101828; --muted:#667085; --line:#e7ebf2; --brand:#3157d5; --canvas:#f6f8fc; --shadow:0 18px 55px rgba(16,24,40,.08); }
        html { scroll-behavior:smooth; }
        body { background:var(--canvas); background-image:radial-gradient(ellipse at 8% 8%,rgba(91,125,255,.11),transparent 34%),radial-gradient(ellipse at 92% 35%,rgba(49,190,151,.09),transparent 30%); color:var(--ink); line-height:1.75; }
        header { min-height:82px; padding:14px clamp(18px,5vw,76px); background:rgba(255,255,255,.86); backdrop-filter:blur(18px); -webkit-backdrop-filter:blur(18px); border-bottom:1px solid rgba(231,235,242,.8); box-shadow:0 5px 25px rgba(16,24,40,.035); }
        .logo-container { gap:13px; }
        .logo-box { width:48px; height:48px; border-radius:15px; background:linear-gradient(145deg,#5478f5,#263fb7); box-shadow:0 8px 20px rgba(49,87,213,.25); }
        .logo-text { font-size:1rem; letter-spacing:-.3px; }
        .logo-text span { color:#98a2b3; font-size:.72rem; }
        nav { gap:3px; }
        nav a { color:#667085; padding:9px 13px; border-radius:11px; font-size:.87rem; }
        nav a:hover, nav a.active { background:#eef2ff; color:var(--brand); }
        .btn-outline { border:1px solid #d8e0f5; color:var(--brand); border-radius:12px; padding:9px 18px; background:#fff; font-weight:700; }
        .btn-outline:hover { background:#eef2ff; border-color:#c5d2ff; }
        .container { width:min(1180px,100%); padding:clamp(38px,6vw,76px) 24px; }
        .page-title { color:var(--ink); font-size:clamp(1.8rem,4vw,2.8rem); line-height:1.35; letter-spacing:-1.1px; margin:0 auto 24px; }
        .page-title:after { content:""; display:block; width:54px; height:4px; border-radius:8px; background:linear-gradient(90deg,#3157d5,#49c6a5); margin:18px auto 0; }
        .hero-card { max-width:930px; padding:clamp(24px,4vw,42px); color:#475467; background:rgba(255,255,255,.84); border:1px solid #fff; border-radius:24px; box-shadow:var(--shadow); line-height:2; font-size:1.02rem; }
        .grid-cards { gap:22px; }
        .card { position:relative; overflow:hidden; min-height:220px; padding:34px 28px; border:1px solid var(--line); border-radius:22px; background:rgba(255,255,255,.96); box-shadow:0 8px 28px rgba(16,24,40,.045); transition:transform .28s,box-shadow .28s,border-color .28s; }
        .card:before { content:""; position:absolute; inset:0 0 auto; height:3px; background:linear-gradient(90deg,#3157d5,#48c6a3); opacity:0; transition:opacity .25s; }
        .card:hover { transform:translateY(-7px); box-shadow:0 20px 45px rgba(35,68,181,.11); border-color:#d9e2ff; }
        .card:hover:before { opacity:1; }
        .card i { display:grid; place-items:center; width:62px; height:62px; margin:0 auto 22px; border-radius:19px; color:var(--brand); background:linear-gradient(145deg,#eef2ff,#e6f8f3); font-size:1.65rem; }
        .card h3 { color:var(--ink); font-size:1.15rem; margin-bottom:10px; }
        .card p { color:var(--muted); line-height:1.9; font-size:.92rem; overflow-wrap:anywhere; }
        .btn-map,.btn-success { border:0; border-radius:12px; background:linear-gradient(135deg,#4268e8,#2849bf); color:#fff; padding:11px 20px; font-weight:700; box-shadow:0 8px 18px rgba(49,87,213,.18); }
        .admin-section { background:rgba(255,255,255,.94); border:1px solid var(--line); border-radius:22px; padding:clamp(20px,3vw,32px); box-shadow:0 10px 30px rgba(16,24,40,.045); }
        .admin-section h3 { color:var(--ink); border-bottom:1px solid var(--line); padding-bottom:15px; }
        .form-group input,.form-group textarea,.form-group select,.admin-form input,.admin-form select { border:1px solid #dce2ed; border-radius:12px; padding:13px 15px; color:var(--ink); background:#fff; transition:.2s; }
        .form-group input:focus,.form-group textarea:focus,.form-group select:focus,.admin-form input:focus,.admin-form select:focus { border-color:#7892f5; box-shadow:0 0 0 4px rgba(49,87,213,.1); }
        .admin-list-item { border:1px solid var(--line); background:#fbfcff; border-radius:14px; }
        .btn-danger,.btn-warning { border-radius:10px; font-weight:700; }
        @media(max-width:900px) { header { gap:12px; } nav { flex-wrap:wrap; justify-content:center; } }
        @media(max-width:768px) { header { position:relative; padding:16px; } .container { padding:36px 16px; } .page-title { font-size:1.75rem!important; } .hero-card { border-radius:18px; } .grid-cards { grid-template-columns:1fr; } .card { min-height:auto; } }

\n        /* ===== ARIO PREMIUM CAMPUS EXPERIENCE ===== */
        :root { --campus-bg:#071426; --campus-panel:rgba(17,35,61,.78); --campus-line:rgba(255,255,255,.12); --campus-text:#f4f7ff; --campus-muted:#a7b7ce; --campus-cyan:#68e5d2; --campus-blue:#83a6ff; }
        body { color:var(--campus-text); background:radial-gradient(ellipse at 9% 10%,rgba(72,117,230,.24),transparent 33%),radial-gradient(ellipse at 92% 78%,rgba(37,198,173,.15),transparent 32%),linear-gradient(135deg,#06101f 0%,#0b1d35 55%,#071426 100%); background-attachment:fixed; }
        body:before { content:"";position:fixed;inset:0;pointer-events:none;z-index:-1;opacity:.16;background-image:linear-gradient(rgba(255,255,255,.045) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.045) 1px,transparent 1px);background-size:52px 52px; }
        header { width:min(1440px,calc(100% - 36px));margin:16px auto 0;padding:12px clamp(14px,3vw,30px);min-height:78px;gap:18px;border:1px solid var(--campus-line);border-radius:22px;background:rgba(10,25,46,.72);backdrop-filter:blur(24px);-webkit-backdrop-filter:blur(24px);box-shadow:0 18px 50px rgba(0,0,0,.22); }
        .logo-box { background:linear-gradient(145deg,#8af3e4,#70a4ff);color:#071b2b;border-radius:15px;box-shadow:0 8px 24px rgba(85,228,210,.2); }
        .logo-text { color:#f5f8ff; } .logo-text span { color:#93a9c5; }
        nav { flex-wrap:wrap;justify-content:center; } nav a { color:#b6c5da;border-radius:12px;transition:.22s; }
        nav a:hover,nav a.active { color:#eafffb;background:rgba(104,229,210,.12); } nav a.active { box-shadow:inset 0 0 0 1px rgba(104,229,210,.16); }
        .auth-btns { align-items:center; } .auth-btns span { color:#a9bad0!important; }
        .btn-outline { color:#9cf0e3;border-color:rgba(104,229,210,.35);background:rgba(104,229,210,.07);border-radius:12px; }
        .btn-outline:hover { color:#071b2b;background:linear-gradient(110deg,#83f0df,#8cb7ff); }
        .container { position:relative;z-index:1;padding-top:clamp(38px,5vw,68px);padding-bottom:80px; }
        .page-title { color:#f5f8ff;text-shadow:0 8px 35px rgba(0,0,0,.2); } .page-title:after { background:linear-gradient(90deg,#76f0dc,#7fa8ff); }
        .hero-card { color:#d0dced;background:linear-gradient(135deg,rgba(255,255,255,.105),rgba(255,255,255,.035));border:1px solid var(--campus-line);border-radius:25px;box-shadow:0 24px 65px rgba(0,0,0,.2),inset 0 1px rgba(255,255,255,.07);backdrop-filter:blur(22px);-webkit-backdrop-filter:blur(22px); }
        .grid-cards { gap:22px; }
        .card { min-height:225px;color:var(--campus-text);background:linear-gradient(145deg,rgba(255,255,255,.105),rgba(255,255,255,.045));border:1px solid var(--campus-line);border-radius:23px;box-shadow:0 15px 40px rgba(0,0,0,.16),inset 0 1px rgba(255,255,255,.055);backdrop-filter:blur(18px);-webkit-backdrop-filter:blur(18px); }
        .card:before { background:linear-gradient(90deg,#76f0dc,#7fa8ff); } .card:hover { border-color:rgba(104,229,210,.32);box-shadow:0 24px 55px rgba(0,0,0,.28),0 0 35px rgba(72,190,190,.07); }
        .card i { color:#9af0e3;background:linear-gradient(145deg,rgba(104,229,210,.16),rgba(131,166,255,.17));border:1px solid rgba(255,255,255,.07); }
        .card h3 { color:#f5f8ff; } .card p { color:#afbed2; }
        .btn-map,.btn-success { background:linear-gradient(110deg,#83f0df,#8cb7ff);color:#071b2b;border-radius:12px;font-weight:850;box-shadow:0 10px 25px rgba(73,183,194,.18); }
        .btn-map:hover,.btn-success:hover { transform:translateY(-2px);filter:brightness(1.04); }
        .admin-section { color:#edf3fc;background:linear-gradient(145deg,rgba(255,255,255,.105),rgba(255,255,255,.045));border:1px solid var(--campus-line)!important;border-radius:22px;box-shadow:0 18px 48px rgba(0,0,0,.17);backdrop-filter:blur(18px); }
        .admin-section h3 { color:#a9f2e6;border-color:rgba(255,255,255,.12); } .admin-section h4 { color:#9eb9ff!important; }
        .admin-list-item { color:#e9f0fb;background:rgba(4,15,29,.42);border:1px solid rgba(255,255,255,.1);border-radius:14px; }
        .admin-list-item span { color:#aebed2!important; } .form-group label { color:#dce7f6; }
        .form-group input,.form-group textarea,.form-group select,.admin-form input,.admin-form select { color:#edf5ff;background:rgba(4,15,29,.62);border:1px solid rgba(255,255,255,.15);border-radius:12px; }
        .form-group input:focus,.form-group textarea:focus,.form-group select:focus,.admin-form input:focus,.admin-form select:focus { border-color:#68dccc;box-shadow:0 0 0 4px rgba(104,229,210,.1);outline:none; }
        input::placeholder,textarea::placeholder { color:#8296b2; } select option { color:#17243a;background:#fff; } .btn-danger { border-radius:10px; }
        @media(max-width:900px) { header { flex-wrap:wrap;justify-content:center; } .logo-container { margin-inline:auto; } nav { order:3;width:100%; } .auth-btns { margin-inline:auto; } }
        @media(max-width:768px) { header { width:calc(100% - 24px);margin-top:12px;border-radius:18px; } nav { gap:4px; } nav a { font-size:.78rem;padding:7px 9px; } .container { padding-inline:15px; } .hero-card { border-radius:19px; } .card { min-height:unset; } }
        @media(prefers-reduced-motion:reduce) { *,*:before,*:after { scroll-behavior:auto!important;transition:none!important; } }

        .home-kicker { width:max-content;max-width:100%;margin:0 auto 18px;padding:8px 15px;border:1px solid rgba(104,229,210,.22);border-radius:30px;background:rgba(104,229,210,.08);color:#a8f5e9;font-size:.8rem;font-weight:750; }
        .home-kicker i { margin-left:7px; }
        .home-container .hero-card { position:relative;overflow:hidden; }
        .home-container .hero-card:before { content:"";position:absolute;width:180px;height:180px;top:-130px;left:8%;border-radius:50%;background:rgba(104,229,210,.13);filter:blur(8px); }
        .admin-list-item form { margin:0; }
        .admin-list-item form button { font-family:inherit; }
        footer { width:min(1180px,calc(100% - 36px));margin:0 auto 22px;padding:18px 22px;text-align:center;color:#8298b5;border:1px solid rgba(255,255,255,.09);border-radius:18px;background:rgba(9,24,44,.55);font-size:.78rem; }
        footer strong { color:#b7d0ef; }
        @media(max-width:768px) { .home-kicker { font-size:.74rem; } footer { width:calc(100% - 24px); } }

        /* خوانایی و تم روشن؛ با انتخاب کاربر در تمام صفحات فعال می‌شود */
        body[data-theme="light"] {
            color:#24324a!important;
            background:radial-gradient(ellipse at 10% 8%,#e3f0ff,transparent 36%),
                       radial-gradient(ellipse at 92% 82%,#e1fbf4,transparent 34%),
                       linear-gradient(135deg,#f8fbff,#eef4fc 55%,#f8fbff)!important;
            background-attachment:fixed!important;
        }
        body[data-theme="light"]:before { opacity:.22; background-image:linear-gradient(rgba(45,72,110,.055) 1px,transparent 1px),linear-gradient(90deg,rgba(45,72,110,.055) 1px,transparent 1px); }
        body[data-theme="light"] header { background:rgba(255,255,255,.78)!important;border-color:rgba(116,139,174,.2)!important;box-shadow:0 14px 38px rgba(36,55,86,.08)!important; }
        body[data-theme="light"] .logo-text { color:#1d2b45!important; }
        body[data-theme="light"] .logo-text span { color:#71829c!important; }
        body[data-theme="light"] nav a { color:#53647e!important; }
        body[data-theme="light"] nav a:hover,body[data-theme="light"] nav a.active { color:#2446a0!important;background:#eaf1ff!important; }
        body[data-theme="light"] .auth-btns span { color:#60718b!important; }
        body[data-theme="light"] .btn-outline { color:#3156bd!important;border-color:#b8c8ef!important;background:rgba(255,255,255,.75)!important; }
        body[data-theme="light"] .page-title { color:#1c3264!important;text-shadow:none!important; }
        body[data-theme="light"] .hero-card { color:#53627a!important;background:rgba(255,255,255,.76)!important;border-color:rgba(255,255,255,.9)!important;box-shadow:0 18px 45px rgba(40,65,105,.08)!important; }
        body[data-theme="light"] .card { color:#263550!important;background:rgba(255,255,255,.86)!important;border-color:#e5ebf5!important;box-shadow:0 12px 34px rgba(35,55,90,.07)!important; }
        body[data-theme="light"] .card h3 { color:#1d3157!important; }
        body[data-theme="light"] .card p { color:#61718a!important; }
        body[data-theme="light"] .card i { color:#4166ce!important;background:#edf2ff!important;border-color:#e2e9ff!important; }
        body[data-theme="light"] .admin-section { color:#2b3b56!important;background:rgba(255,255,255,.88)!important;border-color:#e3eaf4!important;box-shadow:0 12px 34px rgba(35,55,90,.07)!important; }
        body[data-theme="light"] .admin-section h3 { color:#263f7c!important;border-color:#e5eaf3!important; }
        body[data-theme="light"] .admin-section h4 { color:#4765b2!important; }
        body[data-theme="light"] .admin-list-item { color:#33445f!important;background:#f7f9fd!important;border-color:#e4eaf3!important; }
        body[data-theme="light"] .admin-list-item span,body[data-theme="light"] .form-group label { color:#52627a!important; }
        body[data-theme="light"] .form-group input,body[data-theme="light"] .form-group textarea,body[data-theme="light"] .form-group select,body[data-theme="light"] .admin-form input,body[data-theme="light"] .admin-form select { color:#263550!important;background:#fff!important;border-color:#dce4f0!important; }
        body[data-theme="light"] input::placeholder,body[data-theme="light"] textarea::placeholder { color:#9aa8bc!important; }
        body[data-theme="light"] footer { color:#71819a!important;background:rgba(255,255,255,.72)!important;border-color:#e2eaf4!important; }
        body[data-theme="light"] footer strong { color:#38518a!important; }
        body[data-theme="light"] .home-kicker { color:#286f69!important;background:#e8faf6!important;border-color:#c9eee6!important; }
        .theme-toggle {
            display:inline-flex;align-items:center;justify-content:center;gap:10px;
            min-height:44px;padding:7px 13px 7px 9px;border-radius:999px;cursor:pointer;
            color:#e9f4ff;background:linear-gradient(120deg,rgba(255,255,255,.105),rgba(255,255,255,.045));
            border:1px solid rgba(255,255,255,.2);font:750 .78rem 'Vazirmatn',sans-serif;
            white-space:nowrap;transition:background .3s,border-color .3s,box-shadow .3s,transform .3s;
            box-shadow:inset 0 1px rgba(255,255,255,.08),0 5px 18px rgba(0,0,0,.1);
        }
        .theme-toggle:hover { transform:translateY(-1px);border-color:rgba(104,229,210,.55);box-shadow:0 8px 24px rgba(55,190,181,.13); }
        .theme-toggle .theme-icon {
            width:29px;height:29px;display:grid;place-items:center;border-radius:50%;
            color:#082033;background:linear-gradient(145deg,#8af3e4,#8bb5ff);
            box-shadow:0 3px 10px rgba(85,228,210,.2);font-size:.86rem;
        }
        .theme-toggle .theme-label { letter-spacing:-.15px; }
        .theme-toggle .theme-track {
            width:34px;height:19px;padding:3px;border-radius:30px;
            background:rgba(255,255,255,.15);border:1px solid rgba(255,255,255,.13);
            display:flex;align-items:center;justify-content:flex-start;transition:.3s;
        }
        .theme-toggle .theme-track span {
            width:11px;height:11px;border-radius:50%;background:#8cebdc;
            box-shadow:0 0 8px rgba(104,229,210,.5);transition:.3s;
        }
        body[data-theme="light"] .theme-toggle {
            color:#315078;background:linear-gradient(120deg,rgba(255,255,255,.96),rgba(239,246,255,.9));
            border-color:#dce6f3;box-shadow:inset 0 1px #fff,0 6px 18px rgba(49,75,115,.08);
        }
        body[data-theme="light"] .theme-toggle .theme-icon { color:white;background:linear-gradient(145deg,#5d7ee5,#8aa8f6);box-shadow:0 3px 10px rgba(85,120,220,.2); }
        body[data-theme="light"] .theme-toggle .theme-track { justify-content:flex-end;background:#e8edf8;border-color:#dbe4f2; }
        body[data-theme="light"] .theme-toggle .theme-track span { background:#718de9;box-shadow:0 0 8px rgba(113,141,233,.35); }
        @media(max-width:900px) {
            .theme-toggle { min-height:42px;padding:6px 10px 6px 7px; }
            .theme-toggle .theme-label { display:inline!important; }
        }


        /* ===== ARIO / AWARD-INSPIRED EDITORIAL SYSTEM ===== */
        .home-container { width:min(1320px,100%); padding-top:clamp(30px,5vw,66px); }
        .home-hero {
            position:relative; isolation:isolate; overflow:hidden; min-height:510px;
            display:grid; grid-template-columns:minmax(0,1.2fr) minmax(250px,.8fr);
            align-items:center; gap:32px; padding:clamp(28px,5.5vw,76px);
            border:1px solid rgba(159,190,255,.18); border-radius:34px;
            background:
              radial-gradient(ellipse at 12% 8%,rgba(89,125,255,.22),transparent 34%),
              radial-gradient(ellipse at 88% 90%,rgba(104,229,210,.16),transparent 34%),
              linear-gradient(135deg,rgba(17,38,68,.96),rgba(8,22,42,.94));
            box-shadow:0 35px 90px rgba(0,0,0,.28),inset 0 1px rgba(255,255,255,.09);
        }
        .home-hero:before { content:"";position:absolute;inset:0;z-index:-1;opacity:.17;background-image:linear-gradient(rgba(255,255,255,.1) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.1) 1px,transparent 1px);background-size:44px 44px;mask-image:linear-gradient(110deg,#000,transparent 75%); }
        .home-hero:after { content:"";position:absolute;width:390px;height:390px;left:-150px;bottom:-240px;border-radius:50%;border:1px solid rgba(121,235,221,.18);box-shadow:0 0 0 34px rgba(121,235,221,.025),0 0 0 68px rgba(121,235,221,.02); }
        .hero-copy { position:relative;z-index:2;max-width:760px; }
        .home-kicker { margin:0 0 25px;padding:8px 14px;display:inline-flex;align-items:center;gap:9px;border-color:rgba(127,235,220,.28);background:rgba(104,229,210,.09);color:#aaf5e9;letter-spacing:.1px; }
        .home-kicker i { margin:0; }
        .hero-title { max-width:820px;color:#f6f8ff;font-size:clamp(2.5rem,6.3vw,5.7rem);line-height:1.19;letter-spacing:-2.8px;font-weight:900;margin:0 0 23px;text-wrap:balance; }
        .hero-title .title-accent { color:#8cebdc;background:linear-gradient(100deg,#9cf4e5 8%,#8eb4ff 92%);-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent; }
        .hero-subtitle { max-width:650px;color:#bdcbe0;font-size:clamp(.98rem,1.4vw,1.13rem);line-height:2.15;margin-bottom:30px; }
        .hero-actions { display:flex;flex-wrap:wrap;gap:12px;align-items:center; }
        .hero-action { display:inline-flex;align-items:center;justify-content:center;gap:10px;min-height:52px;padding:12px 21px;border-radius:14px;text-decoration:none;font-weight:850;transition:transform .25s,box-shadow .25s,background .25s; }
        .hero-action:hover { transform:translateY(-3px); }
        .hero-action.primary { color:#071b2b;background:linear-gradient(110deg,#8bf0df,#9abaff);box-shadow:0 12px 30px rgba(104,229,210,.2); }
        .hero-action.secondary { color:#e5efff;border:1px solid rgba(255,255,255,.18);background:rgba(255,255,255,.055); }
        .hero-orbit { position:relative;z-index:1;min-height:300px;display:grid;place-items:center; }
        .orbit-ring { position:absolute;width:min(310px,75vw);aspect-ratio:1;border-radius:50%;border:1px solid rgba(142,183,255,.24);box-shadow:0 0 70px rgba(92,137,255,.11),inset 0 0 60px rgba(92,137,255,.07);animation:ario-orbit 24s linear infinite; }
        .orbit-ring:before,.orbit-ring:after { content:"";position:absolute;width:12px;height:12px;border-radius:50%;background:#8cebdc;box-shadow:0 0 22px #8cebdc; }
        .orbit-ring:before { top:16%;right:15%; }.orbit-ring:after { bottom:17%;left:12%;background:#91b5ff;box-shadow:0 0 22px #91b5ff; }
        .orbit-core { position:relative;width:190px;aspect-ratio:1;border-radius:48px;display:grid;place-items:center;transform:rotate(-8deg);background:linear-gradient(145deg,rgba(134,240,222,.17),rgba(117,151,255,.14));border:1px solid rgba(255,255,255,.2);box-shadow:0 25px 70px rgba(0,0,0,.24),inset 0 1px rgba(255,255,255,.2);backdrop-filter:blur(12px); }
        .orbit-core span { transform:rotate(8deg);font-size:6.8rem;font-weight:950;line-height:1;color:#a7f4e8;text-shadow:0 8px 35px rgba(104,229,210,.22); }
        .orbit-tag { position:absolute;bottom:10%;right:0;padding:10px 15px;border-radius:13px;border:1px solid rgba(255,255,255,.14);background:rgba(7,22,42,.8);color:#d7e7fb;font-size:.76rem;font-weight:750;box-shadow:0 12px 28px rgba(0,0,0,.2); }
        .home-metrics { display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:18px 0 64px; }
        .metric { min-height:100px;display:flex;align-items:center;gap:15px;padding:18px 22px;border:1px solid rgba(255,255,255,.1);border-radius:20px;background:rgba(255,255,255,.045); }
        .metric-icon { width:45px;height:45px;flex:0 0 45px;display:grid;place-items:center;border-radius:14px;color:#9df0e3;background:rgba(104,229,210,.1);font-size:1.05rem; }
        .metric strong { display:block;color:#f5f8ff;font-size:1.28rem;line-height:1.4; }
        .metric span:last-child { color:#94a8c2;font-size:.78rem; }
        .home-section-head { display:flex;align-items:end;justify-content:space-between;gap:20px;margin:0 0 23px; }
        .section-eyebrow { display:block;color:#8debdc;font-size:.76rem;font-weight:850;letter-spacing:1.2px;margin-bottom:8px; }
        .home-section-title { color:#f6f8ff;font-size:clamp(1.5rem,3vw,2.3rem);font-weight:900;letter-spacing:-.8px; }
        .section-note { color:#8ea2bd;font-size:.86rem;max-width:290px; }
        .home-container .grid-cards { grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:17px; }
        .home-container .card { min-height:235px;align-items:flex-start;text-align:right;padding:27px 25px;border-radius:21px; }
        .home-container .card i { margin:0 0 21px;width:52px;height:52px;border-radius:16px;font-size:1.35rem; }
        .home-container .card h3 { font-size:1.08rem; }
        .home-container .card p { font-size:.87rem; }
        .home-bottom-note { margin-top:60px;padding:25px 28px;border-top:1px solid rgba(255,255,255,.1);display:flex;justify-content:space-between;align-items:center;gap:18px;color:#8fa4bf;font-size:.83rem; }
        .home-bottom-note strong { color:#d7e8fb; }
        [data-reveal] { opacity:0;transform:translateY(22px);transition:opacity .7s ease,transform .7s cubic-bezier(.2,.7,.2,1); }
        [data-reveal].is-visible { opacity:1;transform:translateY(0); }
        @keyframes ario-orbit { to { transform:rotate(352deg); } }
        @media(max-width:850px) { .home-hero { grid-template-columns:1fr;min-height:unset; } .hero-orbit { min-height:250px; } .orbit-ring { width:235px; } .orbit-core { width:145px;border-radius:38px; } .orbit-core span { font-size:5.2rem; } .orbit-tag { right:10%;bottom:0; } }
        @media(max-width:600px) { .home-container { padding-top:22px; } .home-hero { padding:28px 22px;border-radius:24px;gap:10px; } .hero-title { font-size:clamp(2.35rem,12vw,3.5rem);letter-spacing:-1.7px; } .hero-subtitle { font-size:.93rem; } .hero-actions { display:grid;grid-template-columns:1fr; } .home-metrics { grid-template-columns:1fr;gap:9px;margin-bottom:48px; } .metric { min-height:76px;padding:13px 16px; } .home-section-head { display:block; } .section-note { margin-top:9px; } .home-container .grid-cards { grid-template-columns:1fr; } .home-bottom-note { display:block;text-align:center;line-height:2; } }
        body[data-theme="light"] .home-hero { background:radial-gradient(ellipse at 12% 8%,rgba(89,125,255,.15),transparent 34%),radial-gradient(ellipse at 88% 90%,rgba(45,185,160,.12),transparent 34%),linear-gradient(135deg,#f8fbff,#eaf1ff);border-color:#dce6f7;box-shadow:0 30px 80px rgba(43,73,125,.12); }
        body[data-theme="light"] .hero-title,body[data-theme="light"] .home-section-title,body[data-theme="light"] .metric strong { color:#14233c; }
        body[data-theme="light"] .hero-subtitle,body[data-theme="light"] .section-note { color:#52647e; }
        body[data-theme="light"] .hero-action.secondary { color:#315078;border-color:#d3def0;background:rgba(255,255,255,.68); }
        body[data-theme="light"] .metric { background:rgba(255,255,255,.72);border-color:#dce6f3; }
        body[data-theme="light"] .metric span:last-child,body[data-theme="light"] .home-bottom-note { color:#71819a; }
        body[data-theme="light"] .home-bottom-note { border-color:#dce6f3; }
        body[data-theme="light"] .home-bottom-note strong { color:#315078; }
        body[data-theme="light"] .orbit-tag { color:#315078;background:rgba(255,255,255,.86);border-color:#dbe5f4; }
        body[data-theme="light"] .home-kicker { color:#286f69!important;background:#e8faf6!important;border-color:#c9eee6!important; }
        @media(prefers-reduced-motion:reduce) { .orbit-ring { animation:none!important; } [data-reveal] { opacity:1;transform:none;transition:none; } }


/* ===== ARIO DESIGN SYSTEM — all internal pages ===== */
:root { --ario-bg:#071426; --ario-panel:rgba(15,31,54,.82); --ario-border:rgba(153,183,225,.16); --ario-text:#edf4ff; --ario-muted:#a4b5cc; --ario-accent:#82ebdc; --ario-blue:#8eafff; }
html { scroll-padding-top:100px; }
body:not([data-theme="light"]) { background-color:#071426; background-image:radial-gradient(ellipse at 8% 0%,rgba(62,105,197,.2),transparent 32%),radial-gradient(ellipse at 92% 28%,rgba(35,177,158,.12),transparent 30%),linear-gradient(180deg,#08172b,#071426 65%,#09182b); color:var(--ario-text); }
body:not([data-theme="light"]) header { background:rgba(7,20,38,.78);border-bottom:1px solid rgba(154,185,229,.13);box-shadow:0 12px 35px rgba(0,0,0,.16); }
body:not([data-theme="light"]) .logo-text, body:not([data-theme="light"]) nav a { color:#d7e4f6; }
body:not([data-theme="light"]) .logo-text span { color:#91a7c4; }
body:not([data-theme="light"]) nav a:hover,body:not([data-theme="light"]) nav a.active { color:#a9f4e8;background:rgba(112,164,255,.12); }
body:not([data-theme="light"]) .container { color:var(--ario-text); }
body:not([data-theme="light"]) .page-title { color:#f2f7ff; }
body:not([data-theme="light"]) .page-title:after { background:linear-gradient(90deg,#8cebdc,#8eafff);box-shadow:0 0 22px rgba(115,222,215,.3); }
body:not([data-theme="light"]) .hero-card,body:not([data-theme="light"]) .admin-section { background:linear-gradient(145deg,rgba(20,42,70,.88),rgba(10,27,49,.82));border:1px solid var(--ario-border);box-shadow:0 22px 60px rgba(0,0,0,.18),inset 0 1px rgba(255,255,255,.035);color:#b9c9df; }
body:not([data-theme="light"]) .admin-section h3 { color:#e9f2ff;border-color:rgba(147,184,240,.16); }
body:not([data-theme="light"]) .card { color:#eaf2ff;background:linear-gradient(145deg,rgba(20,42,70,.9),rgba(10,27,49,.88));border-color:var(--ario-border);box-shadow:0 16px 42px rgba(0,0,0,.16); }
body:not([data-theme="light"]) .card h3 { color:#f2f7ff; }
body:not([data-theme="light"]) .card p { color:#a9bad1; }
body:not([data-theme="light"]) .card i { color:#9cf0e3;background:linear-gradient(145deg,rgba(105,225,211,.16),rgba(105,145,255,.14)); }
body:not([data-theme="light"]) .admin-list-item { color:#dce8f8;background:rgba(255,255,255,.045);border-color:rgba(153,183,225,.14); }
body:not([data-theme="light"]) .form-group label { color:#d5e3f5; }
body:not([data-theme="light"]) .form-group input,body:not([data-theme="light"]) .form-group textarea,body:not([data-theme="light"]) .form-group select,body:not([data-theme="light"]) .admin-form input,body:not([data-theme="light"]) .admin-form select { color:#edf4ff;background:rgba(3,14,29,.58);border-color:rgba(157,185,224,.2); }
body:not([data-theme="light"]) input::placeholder,body:not([data-theme="light"]) textarea::placeholder { color:#8298b5; }
body:not([data-theme="light"]) footer { color:#8197b5;border-color:rgba(153,183,225,.13);background:rgba(5,17,32,.35); }
body:not([data-theme="light"]) .btn-outline { color:#a8c0ff;background:rgba(255,255,255,.045);border-color:rgba(145,174,235,.28); }
body:not([data-theme="light"]) .auth-btns span { color:#9fb3cf!important; }
.container { animation:ario-page-in .55s cubic-bezier(.2,.7,.2,1) both; }
@keyframes ario-page-in { from { opacity:0;transform:translateY(12px); } to { opacity:1;transform:translateY(0); } }
header { gap:18px; }
nav a { transition:background .22s,color .22s,transform .22s; }
nav a:hover { transform:translateY(-1px); }
.logo-box { position:relative;overflow:hidden; }
.logo-box:after { content:"";position:absolute;inset:-70% auto -70% -45%;width:35%;transform:rotate(25deg);background:rgba(255,255,255,.25);transition:left .5s; }
.logo-container:hover .logo-box:after { left:120%; }
.page-title { text-wrap:balance; }
.hero-card { text-wrap:pretty; }
.grid-cards .card { text-align:right;align-items:flex-start; }
.grid-cards .card i { margin-right:0; }
button,a,.btn-map,.btn-success,.btn-danger,.btn-warning { -webkit-tap-highlight-color:transparent; }
button,.btn-map,.btn-success,.btn-danger,.btn-warning { transition:transform .2s,box-shadow .2s,filter .2s; }
button:hover,.btn-map:hover,.btn-success:hover,.btn-danger:hover,.btn-warning:hover { transform:translateY(-2px);filter:brightness(1.06); }
input,textarea,select { transition:border-color .2s,box-shadow .2s,background .2s; }
input:focus,textarea:focus,select:focus { outline:none;border-color:#80b0ff!important;box-shadow:0 0 0 4px rgba(105,151,255,.13); }
textarea { min-height:120px;resize:vertical; }
table { width:100%;border-collapse:separate;border-spacing:0;overflow:hidden;border-radius:15px; }
th,td { padding:13px 15px;border-bottom:1px solid rgba(130,155,190,.16); }
th { font-weight:800; }
body:not([data-theme="light"]) th { color:#dceaff;background:rgba(110,150,220,.12); }
body:not([data-theme="light"]) td { color:#bdcce0;background:rgba(255,255,255,.025); }
footer { margin-top:55px;padding:24px 20px;text-align:center;border-top:1px solid #e8edf5;color:#8190a7;font-size:.82rem; }
footer strong { color:inherit; }
.theme-toggle { border-radius:999px!important; }
::selection { background:rgba(112,210,210,.3);color:inherit; }
::-webkit-scrollbar { width:10px; }
::-webkit-scrollbar-track { background:#09182b; }
::-webkit-scrollbar-thumb { background:linear-gradient(#5678d8,#47bca9);border:3px solid #09182b;border-radius:20px; }
body[data-theme="light"] { background-color:#f5f8fe; }
body[data-theme="light"] header { background:rgba(255,255,255,.82); }
body[data-theme="light"] .grid-cards .card { text-align:right;align-items:flex-start; }
body[data-theme="light"] .grid-cards .card i { margin-right:0; }
body[data-theme="light"] .admin-list-item { background:#f8faff;border-color:#e3eaf5;color:#354762; }
@media(max-width:1050px) { header { flex-wrap:wrap;justify-content:center; } .logo-container { margin-inline:auto; } nav { order:3;width:100%;justify-content:center;flex-wrap:wrap; } .auth-btns { margin-inline:auto; } }
@media(max-width:600px) { header { position:sticky;top:0;padding:10px 12px;gap:9px; } .logo-container { gap:9px; } .logo-box { width:39px;height:39px;border-radius:12px; } .logo-text { font-size:.87rem; } nav { gap:2px; } nav a { padding:7px 9px;font-size:.76rem; } .auth-btns { gap:7px;flex-wrap:wrap;justify-content:center; } .auth-btns .theme-toggle { padding:7px 10px; } footer { margin-top:30px;padding:20px 14px; } }
@media(prefers-reduced-motion:reduce) { .container { animation:none; } }

    
/* =============== ARIO SIGNATURE / ART-DIRECTED EDITION =============== */
:root{--sig-bg:#080d18;--sig-panel:#101a2a;--sig-text:#f4f0e8;--sig-muted:#a8b1bf;--sig-line:rgba(255,255,255,.14);--sig-accent:#d8bd8a;--sig-serif:Georgia,'Times New Roman',serif}
body:not([data-theme="light"]){background:#080d18!important;color:var(--sig-text)!important;background-image:radial-gradient(ellipse at 75% 0%,rgba(48,79,112,.25),transparent 35%),linear-gradient(180deg,#080d18,#0b1421 65%,#080d18)!important}
body:not([data-theme="light"]):before{display:none}
header{width:min(1500px,calc(100% - 48px))!important;margin:18px auto 0!important;padding:13px clamp(18px,4vw,54px)!important;min-height:76px!important;border:1px solid rgba(255,255,255,.12)!important;border-radius:3px!important;background:rgba(8,13,24,.84)!important;box-shadow:none!important}
.logo-box{border-radius:2px!important;background:var(--sig-accent)!important;color:#10170a!important;box-shadow:none!important;font-weight:950}
.logo-text{color:#f7f4ed!important;letter-spacing:.2px} .logo-text span{color:#8793a4!important}
nav a{color:#b6c0cf!important;border-radius:2px!important;font-size:.82rem!important;letter-spacing:.1px}
nav a:hover,nav a.active{background:rgba(216,189,138,.1)!important;color:var(--sig-accent)!important}
.btn-outline{border-radius:2px!important;color:var(--sig-accent)!important;border-color:rgba(216,189,138,.5)!important;background:transparent!important}
.theme-toggle{border:1px solid var(--sig-line)!important;border-radius:2px!important;background:transparent!important;color:#dbe4ef!important;padding:9px 13px!important;cursor:pointer}
footer{border-color:var(--sig-line)!important;color:#8390a2!important;background:transparent!important;letter-spacing:.3px}
.signature-home{width:100%;overflow:hidden}.signature-hero{height:min(760px,82vh);min-height:590px;position:relative;display:flex;align-items:center;padding:clamp(35px,9vw,150px);margin:0;width:100%;overflow:hidden;background:#101a29;border-radius:0!important;box-shadow:none!important;border:0!important}
.hero-photo{position:absolute;inset:0;background-image:url('https://images.unsplash.com/photo-1523050854058-8df90110c9f1?auto=format&fit=crop&w=2200&q=92');background-size:cover;background-position:center 42%;transform:scale(1.02);animation:heroDrift 24s ease-in-out infinite alternate}
@keyframes heroDrift{to{transform:scale(1.09) translateX(-1.2%)}}
.hero-shade{position:absolute;inset:0;background:linear-gradient(90deg,rgba(4,9,16,.92) 0%,rgba(4,9,16,.72) 43%,rgba(4,9,16,.12) 100%),linear-gradient(0deg,rgba(4,9,16,.6),transparent 40%)}
.hero-grain{position:absolute;inset:0;opacity:.14;pointer-events:none;background-image:url("data:image/svg+xml,%3Csvg viewBox='0 0 180 180' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.8' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='.22'/%3E%3C/svg%3E")}
.hero-content{position:relative;z-index:2;max-width:790px}.hero-overline,.section-eyebrow{display:flex;align-items:center;gap:12px;color:var(--sig-accent);font-size:.72rem;font-weight:800;letter-spacing:2px}.overline-line{height:1px;width:35px;background:var(--sig-accent)}.overline-en{color:#c1cad5;font-size:.64rem;letter-spacing:1.8px;margin-right:8px}
.hero-content h1{font-size:clamp(2.8rem,6.8vw,6.8rem);line-height:1.27;letter-spacing:-2.8px;color:#fff;font-weight:950;margin:32px 0 20px;text-wrap:balance}.hero-content h1 em,.simple-page-heading h1 em,.inner-hero-copy h1 em,.story-side h2 em{font-family:var(--sig-serif);font-weight:400;color:var(--sig-accent);font-style:italic;letter-spacing:-1px}.hero-content p{max-width:600px;color:#d1d7df;font-size:1rem;line-height:2.1}.hero-cta{display:flex;gap:13px;align-items:center;margin-top:34px;flex-wrap:wrap}.cta-solid,.cta-ghost{display:inline-flex;align-items:center;gap:20px;text-decoration:none;padding:15px 22px;font-size:.86rem;font-weight:850;transition:.25s;border-radius:2px}.cta-solid{background:var(--sig-accent);color:#11180b}.cta-ghost{color:white;border:1px solid rgba(255,255,255,.4);background:rgba(255,255,255,.04)}.cta-solid:hover,.cta-ghost:hover{transform:translateY(-4px)}.hero-caption{position:absolute;z-index:2;bottom:32px;right:clamp(30px,5vw,75px);left:clamp(30px,5vw,75px);display:flex;align-items:center;gap:18px;color:#d6dce5;font-size:.68rem;letter-spacing:1.2px}.hero-caption span:first-child{color:var(--sig-accent)}.caption-line{height:1px;flex:1;background:rgba(255,255,255,.35)}.hero-scroll{position:absolute;z-index:2;left:clamp(30px,5vw,75px);bottom:32px;color:#d6dce5;font-size:.62rem;letter-spacing:1.7px;display:flex;gap:12px;align-items:center}.hero-scroll i{color:var(--sig-accent)}
.intro-strip{width:min(1250px,calc(100% - 64px));margin:0 auto;padding:95px 0 78px;display:grid;grid-template-columns:.65fr 1.5fr;gap:50px;align-items:start;border-bottom:1px solid var(--sig-line)}.intro-label{font-size:.72rem;color:var(--sig-accent);letter-spacing:1.8px;font-weight:850;padding-top:10px}.intro-strip p{font-size:clamp(1.55rem,3vw,2.7rem);line-height:1.75;color:#e9edf2;font-weight:400;margin:0;max-width:900px}.intro-strip strong{color:var(--sig-accent);font-weight:850}
.home-stats{width:min(1250px,calc(100% - 64px));margin:0 auto;padding:50px 0 80px;display:grid;grid-template-columns:repeat(4,1fr);gap:25px}.home-stats>div{border-left:1px solid var(--sig-line);padding:5px 24px 5px 0;display:flex;flex-direction:column;gap:8px}.home-stats strong{font-family:var(--sig-serif);font-size:3.3rem;font-weight:400;color:var(--sig-accent);line-height:1}.home-stats span{color:#a9b4c3;font-size:.82rem}.home-stats .stats-note{font-size:.7rem;letter-spacing:3px;color:#9aa8ba;justify-content:center;line-height:1.8}.stats-note b{font-size:1.7rem;color:#fff;letter-spacing:5px}
.editorial-section{width:min(1250px,calc(100% - 64px));margin:0 auto;padding:40px 0 115px}.section-heading{display:flex;justify-content:space-between;align-items:end;gap:40px;margin-bottom:45px}.section-heading h2{font-size:clamp(2.2rem,4.5vw,4.5rem);line-height:1.35;margin-top:18px;letter-spacing:-1.8px}.section-heading h2 em{font-family:var(--sig-serif);font-weight:400;color:var(--sig-accent)}.section-heading>p{max-width:380px;color:#9ba8b9;line-height:2;font-size:.9rem;padding-bottom:8px}.editorial-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:20px}.editorial-card{position:relative;min-height:420px;background:#101b2a;border:1px solid var(--sig-line);overflow:hidden;transition:.35s}.editorial-card:nth-child(3n+2){transform:translateY(42px)}.editorial-card:hover{transform:translateY(-8px)}.editorial-card:nth-child(3n+2):hover{transform:translateY(32px)}.editorial-card-image{height:210px;background-size:cover;background-position:center;filter:saturate(.75);transition:transform .6s}.editorial-card:hover .editorial-card-image{transform:scale(1.06)}.editorial-card-body{padding:24px 25px 30px;position:relative}.card-index{position:absolute;left:22px;top:24px;color:#748399;font-family:var(--sig-serif);font-size:1.1rem}.editorial-card-body>i{color:var(--sig-accent);font-size:1.1rem;margin-bottom:18px}.editorial-card h3{font-size:1.18rem;margin:0 0 10px;color:#f4f3ef}.editorial-card p{font-size:.86rem;line-height:1.9;color:#a6b1c1}.feature-band{width:min(1500px,calc(100% - 48px));margin:35px auto 0;min-height:530px;display:grid;grid-template-columns:1.05fr .95fr;background:#111d2c}.feature-band-image{background:url('https://images.unsplash.com/photo-1498243691581-b145c3f54a5a?auto=format&fit=crop&w=1500&q=90') center/cover;min-height:530px}.feature-band-copy{padding:clamp(35px,6vw,85px);display:flex;flex-direction:column;justify-content:center}.feature-band-copy h2{font-size:clamp(2.3rem,4vw,4.5rem);line-height:1.4;margin:25px 0}.feature-band-copy p{color:#aab6c5;line-height:2;max-width:470px}.text-link{color:var(--sig-accent);text-decoration:none;margin-top:30px;font-size:.85rem;font-weight:800}.text-link i{margin-right:10px}.home-bottom-cta{width:min(1250px,calc(100% - 64px));margin:0 auto;padding:45px 0 70px;display:flex;justify-content:space-between;align-items:center;gap:20px;color:#f1f3f5;font-size:1.3rem}.home-bottom-cta span{font-family:var(--sig-serif);font-style:italic;font-size:2rem}.home-bottom-cta a{color:var(--sig-accent);text-decoration:none;font-size:.85rem}
.inner-page{width:min(1350px,calc(100% - 48px));margin:18px auto 0;padding-bottom:90px}.inner-hero{height:540px;position:relative;display:flex;align-items:end;overflow:hidden}.inner-hero-image{position:absolute;inset:0;background-size:cover;background-position:center}.inner-hero-overlay{position:absolute;inset:0;background:linear-gradient(0deg,rgba(5,11,19,.95),rgba(5,11,19,.1) 90%),linear-gradient(90deg,rgba(5,11,19,.45),transparent)}.inner-hero-copy{position:relative;z-index:2;padding:clamp(30px,7vw,95px)}.inner-hero-copy h1{font-size:clamp(3.1rem,6vw,6rem);line-height:1.25;margin:20px 0}.inner-hero-copy p{color:#d0d8e3;font-size:1rem}.story-layout{width:min(1120px,calc(100% - 50px));margin:0 auto;padding:100px 0;display:grid;grid-template-columns:.65fr 1.35fr;gap:80px}.story-side>span{font-size:.68rem;color:var(--sig-accent);letter-spacing:2px}.story-side h2{font-size:3.4rem;line-height:1.35;margin-top:20px}.story-main{border-right:1px solid var(--sig-line);padding-right:45px;color:#aeb9c8;line-height:2.2;font-size:.95rem}.story-main p+p{margin-top:18px}.story-main .story-lead{font-size:1.5rem;color:#f2f3f1;line-height:1.9}.values-row{width:min(1120px,calc(100% - 50px));margin:0 auto;display:grid;grid-template-columns:repeat(3,1fr);border-top:1px solid var(--sig-line);border-bottom:1px solid var(--sig-line)}.values-row article{padding:35px 28px;border-left:1px solid var(--sig-line);position:relative}.values-row article>span{position:absolute;left:22px;top:25px;color:#738198;font-family:var(--sig-serif)}.values-row i{color:var(--sig-accent);font-size:1.5rem;margin-bottom:25px}.values-row h3{font-size:1.2rem;margin-bottom:10px}.values-row p{color:#9eabba;font-size:.85rem;line-height:1.9}
.compact-inner{padding-top:65px}.simple-page-heading{padding:25px 0 65px;max-width:850px}.simple-page-heading h1{font-size:clamp(3rem,6vw,6rem);line-height:1.28;margin:20px 0}.simple-page-heading h1 em{color:var(--sig-accent)}.simple-page-heading>p{color:#a8b4c4;font-size:1rem;line-height:2;max-width:620px}.people-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}.person-card{min-height:275px;padding:34px;background:linear-gradient(145deg,#111e30,#0c1726);border:1px solid var(--sig-line);position:relative;transition:.3s}.person-card:hover{transform:translateY(-7px);border-color:rgba(216,189,138,.45)}.person-avatar{width:74px;height:74px;border-radius:50%;display:grid;place-items:center;background:rgba(216,189,138,.1);border:1px solid rgba(216,189,138,.24);color:var(--sig-accent);font-size:1.6rem;margin-bottom:28px}.person-no{position:absolute;left:28px;top:38px;color:#7c899c;font-size:.65rem;letter-spacing:1.4px}.person-card h3{font-size:1.2rem;margin-bottom:9px}.person-card p{color:#a7b3c2;font-size:.9rem;line-height:1.9}.activity-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:22px}.activity-card{background:#101c2c;border:1px solid var(--sig-line);overflow:hidden}.activity-photo{height:285px;background-size:cover;background-position:center;position:relative}.activity-photo:after,.news-photo:after{content:"";position:absolute;inset:0;background:linear-gradient(0deg,rgba(4,9,16,.55),transparent 55%)}.activity-photo span,.news-photo span{position:absolute;z-index:1;right:22px;bottom:18px;color:white;font-size:.65rem;letter-spacing:1.7px}.activity-copy{padding:25px 28px 32px}.activity-copy>i{color:var(--sig-accent);font-size:1.2rem}.activity-copy h3{font-size:1.35rem;margin:14px 0 8px}.activity-copy p{color:#a8b4c4;line-height:1.95;font-size:.9rem}.news-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:20px}.news-card{background:#101c2c;border:1px solid var(--sig-line);overflow:hidden;transition:.3s}.news-card:hover{transform:translateY(-6px)}.news-photo{height:230px;background-size:cover;background-position:center;position:relative}.news-copy{padding:24px}.news-date{font-size:.7rem;color:var(--sig-accent);letter-spacing:.7px}.news-copy h3{font-size:1.2rem;margin:12px 0}.news-copy p{font-size:.88rem;color:#a8b4c4;line-height:2}.empty-state{grid-column:1/-1;padding:45px;border:1px dashed var(--sig-line);color:#a9b4c3;text-align:center}
.contact-page{padding-top:65px}.contact-layout{display:grid;grid-template-columns:.8fr 1.2fr;gap:22px}.contact-info{display:grid;grid-template-columns:1fr 1fr;gap:15px}.contact-item{padding:30px;background:#111e30;border:1px solid var(--sig-line);min-height:245px}.contact-item>span{display:block;color:var(--sig-accent);font-size:.65rem;letter-spacing:1.7px;margin-bottom:25px}.contact-item>i{font-size:1.35rem;color:var(--sig-accent);margin-bottom:18px}.contact-item h3{font-size:1.1rem;margin-bottom:10px}.contact-item p{font-size:.84rem;color:#aab6c6;line-height:1.9}.contact-item a{display:inline-block;color:var(--sig-accent);font-size:.8rem;text-decoration:none;margin-top:17px}.contact-image{min-height:505px;background:url('https://images.unsplash.com/photo-1562774053-701939374585?auto=format&fit=crop&w=1400&q=90') center/cover;position:relative}.contact-image:after{content:"";position:absolute;inset:0;background:linear-gradient(0deg,rgba(4,10,18,.78),transparent 75%)}.contact-image-overlay{position:absolute;z-index:1;bottom:35px;right:35px}.contact-image-overlay span{display:block;color:var(--sig-accent);font-size:.65rem;letter-spacing:1.8px;margin-bottom:15px}.contact-image-overlay strong{font-size:2.3rem;line-height:1.5}
body[data-theme="light"]{background:#f3f1e9!important;color:#18212d!important}body[data-theme="light"] header{background:rgba(247,246,239,.92)!important;border-color:#d8d8ce!important}body[data-theme="light"] .logo-text,body[data-theme="light"] nav a{color:#273244!important}body[data-theme="light"] nav a.active,body[data-theme="light"] nav a:hover{color:#405a12!important;background:rgba(120,150,50,.12)!important}body[data-theme="light"] .signature-hero,body[data-theme="light"] .inner-hero{filter:none}body[data-theme="light"] .intro-strip p,body[data-theme="light"] .section-heading h2,body[data-theme="light"] .home-bottom-cta,body[data-theme="light"] .simple-page-heading h1,body[data-theme="light"] .story-side h2{color:#172333}body[data-theme="light"] .editorial-card,body[data-theme="light"] .feature-band,body[data-theme="light"] .person-card,body[data-theme="light"] .activity-card,body[data-theme="light"] .news-card,body[data-theme="light"] .contact-item{background:#fff;border-color:#dfe2d9;color:#172333}body[data-theme="light"] .editorial-card h3,body[data-theme="light"] .activity-copy h3,body[data-theme="light"] .news-copy h3,body[data-theme="light"] .person-card h3,body[data-theme="light"] .contact-item h3{color:#172333}body[data-theme="light"] .editorial-card p,body[data-theme="light"] .activity-copy p,body[data-theme="light"] .news-copy p,body[data-theme="light"] .person-card p,body[data-theme="light"] .contact-item p,body[data-theme="light"] .section-heading>p,body[data-theme="light"] .simple-page-heading>p,body[data-theme="light"] .story-main{color:#5d6876}body[data-theme="light"] .story-main .story-lead{color:#1d2939}body[data-theme="light"] .values-row,body[data-theme="light"] .values-row article{border-color:#d8ddd4}body[data-theme="light"] .values-row h3{color:#1d2939}body[data-theme="light"] .values-row p{color:#647083}body[data-theme="light"] .home-stats span{color:#5f6b7b}body[data-theme="light"] .home-bottom-cta a{color:#526c18}body[data-theme="light"] footer{color:#687486}
@media(max-width:900px){.signature-hero{min-height:600px;height:76vh;padding:45px}.intro-strip{grid-template-columns:1fr;gap:20px;padding:65px 0}.home-stats{grid-template-columns:repeat(2,1fr)}.editorial-grid,.news-grid,.people-grid{grid-template-columns:repeat(2,1fr)}.editorial-card:nth-child(3n+2){transform:none}.editorial-card:nth-child(3n+2):hover{transform:translateY(-8px)}.feature-band{grid-template-columns:1fr}.feature-band-image{min-height:330px}.story-layout{gap:35px}.contact-layout{grid-template-columns:1fr}.contact-image{min-height:380px}}
@media(max-width:600px){header{width:calc(100% - 20px)!important;margin-top:10px!important}.signature-hero{width:100%;margin-top:0;min-height:620px;height:78vh;padding:28px;border-radius:0!important}.hero-content h1{font-size:2.65rem;letter-spacing:-1.3px}.hero-content p{font-size:.88rem}.hero-caption{bottom:25px;right:22px;left:22px}.hero-scroll{display:none}.intro-strip,.home-stats,.editorial-section,.home-bottom-cta{width:calc(100% - 42px)}.intro-strip p{font-size:1.55rem}.home-stats{gap:20px}.home-stats strong{font-size:2.6rem}.section-heading{display:block}.section-heading>p{margin-top:20px}.editorial-grid,.news-grid,.people-grid,.activity-grid{grid-template-columns:1fr}.editorial-card{min-height:0}.editorial-card-image{height:210px}.feature-band{width:calc(100% - 20px)}.feature-band-image{min-height:250px}.feature-band-copy{padding:30px 25px}.home-bottom-cta{align-items:flex-start;flex-direction:column}.home-bottom-cta span{font-size:1.7rem}.inner-page{width:calc(100% - 20px)}.inner-hero{height:470px}.inner-hero-copy{padding:28px}.inner-hero-copy h1{font-size:3.2rem}.compact-inner{padding-top:45px}.simple-page-heading{padding-bottom:40px}.simple-page-heading h1{font-size:3.2rem}.story-layout{width:calc(100% - 30px);padding:60px 0;grid-template-columns:1fr;gap:25px}.story-side h2{font-size:2.6rem}.story-main{padding-right:20px}.values-row{width:calc(100% - 30px);grid-template-columns:1fr}.values-row article{border-left:0;border-bottom:1px solid var(--sig-line)}.contact-info{grid-template-columns:1fr}.contact-image{min-height:330px}.contact-image-overlay strong{font-size:1.8rem}.hero-cta{gap:9px}.cta-solid,.cta-ghost{padding:13px 15px;font-size:.78rem}}
@media(prefers-reduced-motion:reduce){.hero-photo{animation:none}.editorial-card,.person-card,.news-card{transition:none}}


/* ===== ARIO REFINED NAVY + CHAMPAGNE / SOFT-CURVE SYSTEM ===== */
:root{
 --sig-accent:#d8bd8a!important;
 --ario-accent:#d8bd8a;
 --ario-blue:#9bb8ed;
 --ario-radius:28px;
}
body:not([data-theme="light"]){
 background-color:#071426!important;
 background-image:
 radial-gradient(ellipse at 82% 0%,rgba(92,128,184,.20),transparent 34%),
 radial-gradient(ellipse at 8% 75%,rgba(74,105,151,.12),transparent 32%),
 linear-gradient(145deg,#071426 0%,#0b1b31 54%,#081426 100%)!important;
}
header{
 border-radius:26px!important;
 border-color:rgba(216,189,138,.20)!important;
 box-shadow:0 18px 55px rgba(0,0,0,.22),inset 0 1px rgba(255,255,255,.035)!important;
}
.logo-box{
 border-radius:17px 8px 17px 8px!important;
 background:linear-gradient(145deg,#e4cfaa,#b99a68)!important;
 color:#102039!important;
 box-shadow:0 9px 24px rgba(216,189,138,.16)!important;
}
nav a,.btn-outline,.theme-toggle{
 border-radius:999px!important;
}
nav a:hover,nav a.active{
 color:#f0d9ad!important;
 background:rgba(216,189,138,.12)!important;
}
.btn-outline{
 color:#e0c99e!important;
 border-color:rgba(216,189,138,.42)!important;
 background:rgba(216,189,138,.055)!important;
}
.btn-outline:hover{background:rgba(216,189,138,.14)!important}
.page-title:after{
 background:linear-gradient(90deg,#9bb8ed,#d8bd8a)!important;
 border-radius:999px!important;
}
.hero-card,.admin-section{
 border-radius:32px 14px 32px 14px!important;
 border-color:rgba(216,189,138,.17)!important;
}
.card,.editorial-card,.person-card,.activity-card,.news-card,.contact-item,
.feature-band,.contact-image,.inner-hero,.signature-hero{
 border-radius:28px 10px 28px 10px!important;
 overflow:hidden;
}
.card{
 border-color:rgba(216,189,138,.16)!important;
}
.card:before{background:linear-gradient(90deg,#9bb8ed,#d8bd8a)!important}
.card:hover,.editorial-card:hover,.person-card:hover,.news-card:hover{
 border-color:rgba(216,189,138,.42)!important;
}
.card i,.person-avatar{
 color:#e2c99a!important;
 background:linear-gradient(145deg,rgba(155,184,237,.15),rgba(216,189,138,.12))!important;
 border-color:rgba(216,189,138,.2)!important;
 border-radius:20px 8px 20px 8px!important;
}
.btn-map,.btn-success,.cta-solid{
 color:#13233a!important;
 background:linear-gradient(115deg,#d8bd8a,#ead9b7)!important;
 border-radius:999px!important;
 box-shadow:0 10px 28px rgba(216,189,138,.15)!important;
}
.cta-ghost{border-radius:999px!important}
.home-kicker,.eyebrow{
 color:#e4cda3!important;
 border-color:rgba(216,189,138,.28)!important;
 background:rgba(216,189,138,.08)!important;
}
.hero-content h1 em,.simple-page-heading h1 em,.inner-hero-copy h1 em,
.story-side h2 em,.section-heading h2 em{color:#dfc69a!important}
.section-heading h2 em{color:#dfc69a!important}
.text-link,.news-date,.activity-copy>i,.contact-item>span,
.contact-item>i,.contact-item a,.values-row i,.values-row article>span{
 color:#dfc69a!important;
}
.person-card:hover{border-color:rgba(216,189,138,.42)!important}
.admin-section h3{color:#e8d3ad!important}
.form-group input:focus,.form-group textarea:focus,.form-group select:focus,
.admin-form input:focus,.admin-form select:focus{
 border-color:#b7c9e9!important;
 box-shadow:0 0 0 4px rgba(155,184,237,.13)!important;
}
footer{border-color:rgba(216,189,138,.16)!important}
::selection{background:rgba(216,189,138,.32)!important}
::-webkit-scrollbar-thumb{background:linear-gradient(#8faee5,#d8bd8a)!important}
body[data-theme="light"]{
 background:#f2f4f8!important;
 color:#17243a!important;
}
body[data-theme="light"] header{
 background:rgba(249,250,253,.94)!important;
 border-color:#dce3ee!important;
}
body[data-theme="light"] nav a:hover,
body[data-theme="light"] nav a.active{
 color:#314e7c!important;
 background:rgba(155,184,237,.18)!important;
}
body[data-theme="light"] .page-title:after{background:linear-gradient(90deg,#789bd5,#c5a16a)!important}
body[data-theme="light"] .hero-card,
body[data-theme="light"] .admin-section,
body[data-theme="light"] .card{
 background:rgba(255,255,255,.94)!important;
 border-color:#e1e6ef!important;
 color:#27364b!important;
}
body[data-theme="light"] .card h3,
body[data-theme="light"] .admin-section h3{color:#17243a!important}
body[data-theme="light"] .card i{color:#536f9f!important}
body[data-theme="light"] .btn-map,
body[data-theme="light"] .btn-success{color:#17243a!important}
@media(max-width:768px){
 header{border-radius:20px!important}
 .signature-hero,.inner-hero{border-radius:24px 9px 24px 9px!important}
 .card,.editorial-card,.person-card,.activity-card,.news-card,.contact-item{
  border-radius:22px 9px 22px 9px!important;
 }
}


/* ARIO HOME REFINEMENT — clear navy, porcelain and periwinkle */
.signature-home [data-reveal]{opacity:1!important;transform:none!important}
.signature-hero{border-radius:0!important;box-shadow:none!important;background:#101f38!important}
.hero-photo{filter:saturate(.78) contrast(1.04)}
.hero-shade{background:linear-gradient(90deg,rgba(7,17,34,.94),rgba(8,22,43,.77) 48%,rgba(9,24,45,.24))!important}
.hero-content h1{color:#f7f8fc!important;text-shadow:0 5px 28px rgba(0,0,0,.24)}
.hero-content h1 em{color:#b7c9f4!important}
.hero-content p{color:#d1d9e8!important}
.hero-overline,.section-eyebrow,.intro-label{color:#b6c8f2!important}
.overline-line{background:#9db4ec!important}
.cta-solid{color:#101d35!important;background:linear-gradient(135deg,#dce5fb,#aebfe9)!important;border-radius:999px 999px 999px 8px!important;box-shadow:0 12px 28px rgba(121,151,218,.23)!important}
.cta-ghost{color:#f2f5fc!important;border:1px solid rgba(219,229,250,.34)!important;border-radius:999px!important;background:rgba(255,255,255,.07)!important}
.intro-strip{border-color:rgba(174,194,232,.18)!important}
.intro-strip p{color:#e8edf7!important}.intro-strip strong{color:#b7c9f4!important}
.home-stats>div{border-color:rgba(174,194,232,.2)!important}
.home-stats strong{color:#c0cef0!important}.home-stats span,.home-stats .stats-note{color:#aebbd0!important}.stats-note b{color:#e6ebf7!important}
.editorial-section{padding-top:55px!important}
.section-heading{align-items:end;margin-bottom:38px!important}
.section-heading h2{color:#f4f6fb!important}.section-heading h2 em{color:#b9c9ee!important}.section-heading>p{color:#b4bfd1!important}
.editorial-grid{gap:22px!important;align-items:stretch}
.editorial-card{min-height:430px!important;border:1px solid rgba(183,199,229,.17)!important;border-radius:26px 26px 26px 8px!important;background:linear-gradient(155deg,#172943,#101e34)!important;box-shadow:0 18px 45px rgba(0,0,0,.18)!important;overflow:hidden}
.editorial-card:nth-child(3n+2){transform:translateY(22px)!important}
.editorial-card:hover,.editorial-card:nth-child(3n+2):hover{transform:translateY(-7px)!important;border-color:rgba(181,200,244,.48)!important;box-shadow:0 28px 55px rgba(0,0,0,.28)!important}
.editorial-card-image{height:235px!important;filter:saturate(.82) contrast(1.02)!important;position:relative}
.editorial-card-body{padding:25px 27px 32px!important}
.editorial-card-body>i{display:inline-grid;place-items:center;width:46px;height:46px;border-radius:15px 15px 15px 5px;color:#c8d5f4!important;background:rgba(164,187,237,.12);border:1px solid rgba(190,207,245,.16)}
.editorial-card h3{color:#f5f7fc!important;font-size:1.2rem!important}
.editorial-card p{color:#b9c5d7!important;line-height:2!important}.card-index{color:#aab9d4!important}
.feature-band{border-radius:30px 30px 30px 8px!important;overflow:hidden;background:linear-gradient(135deg,#172943,#101d32)!important;border:1px solid rgba(183,199,229,.16);box-shadow:0 24px 65px rgba(0,0,0,.2)}
.feature-band-image{filter:saturate(.78) contrast(1.03)}
.feature-band-copy h2{color:#f5f7fc!important}.feature-band-copy p{color:#bdc8d9!important}
.text-link,.home-bottom-cta a{color:#c1d0f3!important}
.home-bottom-cta{color:#e9eef8!important;border-color:rgba(174,194,232,.18)}
.home-bottom-cta span{color:#c4d0ec!important}
body[data-theme="light"] .signature-home{color:#1b2940}
body[data-theme="light"] .intro-strip p,body[data-theme="light"] .section-heading h2,body[data-theme="light"] .home-bottom-cta{color:#1b2940!important}
body[data-theme="light"] .intro-strip strong,body[data-theme="light"] .section-heading h2 em,body[data-theme="light"] .section-eyebrow,body[data-theme="light"] .intro-label{color:#526da8!important}
body[data-theme="light"] .editorial-card,body[data-theme="light"] .feature-band{background:linear-gradient(145deg,#fff,#f1f5fc)!important;border-color:#dce4f2!important;box-shadow:0 18px 42px rgba(35,55,91,.09)!important}
body[data-theme="light"] .editorial-card h3,body[data-theme="light"] .feature-band-copy h2{color:#1b2940!important}
body[data-theme="light"] .editorial-card p,body[data-theme="light"] .feature-band-copy p,body[data-theme="light"] .section-heading>p{color:#596981!important}
body[data-theme="light"] .editorial-card-body>i{color:#526da8!important;background:#eaf0fc;border-color:#dce5f7}
body[data-theme="light"] .home-stats strong{color:#526da8!important}
body[data-theme="light"] .home-stats span{color:#62718a!important}
body[data-theme="light"] .home-stats>div,body[data-theme="light"] .intro-strip,body[data-theme="light"] .home-bottom-cta{border-color:#dce4f0!important}
body[data-theme="light"] .home-bottom-cta span{color:#344b77!important}
@media(max-width:900px){.editorial-card:nth-child(3n+2){transform:none!important}.editorial-card:nth-child(3n+2):hover{transform:translateY(-7px)!important}}
@media(max-width:600px){.signature-hero{border-radius:0!important}.editorial-card{border-radius:22px 22px 22px 7px!important}.feature-band{border-radius:23px 23px 23px 7px!important}}


/* FINAL POLISH — glass header, stable reveal, editorial staff rows */
header:not(.topbar){
  position:sticky!important;top:10px!important;z-index:1200!important;
  width:min(1500px,calc(100% - 48px))!important;
  margin:12px auto 0!important;
  background:rgba(12,27,48,.58)!important;
  border:1px solid rgba(205,220,245,.20)!important;
  border-radius:24px!important;
  -webkit-backdrop-filter:blur(24px) saturate(145%)!important;
  backdrop-filter:blur(24px) saturate(145%)!important;
  box-shadow:0 14px 42px rgba(0,0,0,.18),inset 0 1px rgba(255,255,255,.08)!important;
}
body[data-theme="light"] header:not(.topbar){
  background:rgba(249,252,255,.68)!important;
  border-color:rgba(118,143,181,.22)!important;
  -webkit-backdrop-filter:blur(24px) saturate(150%)!important;
  backdrop-filter:blur(24px) saturate(150%)!important;
  box-shadow:0 14px 38px rgba(35,55,88,.09)!important;
}
body[data-theme="light"] header:not(.topbar) .logo-text,
body[data-theme="light"] header:not(.topbar) nav a{color:#263a5b!important}
body[data-theme="light"] header:not(.topbar) nav a.active,
body[data-theme="light"] header:not(.topbar) nav a:hover{color:#365b9b!important;background:rgba(116,151,215,.13)!important}
body[data-theme="light"] header:not(.topbar) .btn-outline{color:#365b9b!important;border-color:rgba(88,122,184,.38)!important}
body[data-theme="light"] header:not(.topbar) .theme-toggle{color:#365b9b!important}

/* Do not leave page copy hidden if the observer misses an element */
[data-reveal]{opacity:1!important;transform:none!important}
[data-reveal].is-visible{opacity:1!important;transform:none!important}
.people-grid{display:flex!important;flex-direction:column!important;gap:14px!important;width:100%!important}
.person-card{
  width:100%!important;min-height:0!important;display:grid!important;
  grid-template-columns:88px minmax(0,1fr) auto!important;
  grid-template-rows:auto auto!important;align-items:center!important;
  column-gap:24px!important;row-gap:5px!important;
  padding:22px 28px!important;margin:0!important;
  border-radius:22px 22px 22px 7px!important;
  background:linear-gradient(105deg,rgba(24,44,72,.94),rgba(14,29,50,.94))!important;
  border:1px solid rgba(174,197,233,.17)!important;
  box-shadow:0 12px 30px rgba(0,0,0,.13)!important;
}
.person-card .person-avatar{grid-column:1;grid-row:1/3;width:70px!important;height:70px!important;margin:0!important}
.person-card .person-no{position:static!important;grid-column:3;grid-row:1;color:#9eb4d7!important;text-align:left}
.person-card h3{grid-column:2;grid-row:1;margin:0 0 3px!important;font-size:1.15rem!important;color:#f3f6fc!important}
.person-card p{grid-column:2;grid-row:2;margin:0!important;color:#b8c6d9!important;line-height:1.9!important}
body[data-theme="light"] .person-card{
  background:linear-gradient(105deg,#fff,#f1f5fc)!important;
  border-color:#dce5f2!important;box-shadow:0 10px 26px rgba(44,66,105,.07)!important
}
body[data-theme="light"] .person-card h3{color:#20324e!important}
body[data-theme="light"] .person-card p{color:#61718a!important}
body[data-theme="light"] .person-card .person-no{color:#7187ac!important}
@media(max-width:650px){
  header:not(.topbar){width:calc(100% - 20px)!important;top:6px!important;margin-top:8px!important}
  .people-grid{gap:11px!important}
  .person-card{grid-template-columns:58px minmax(0,1fr)!important;padding:17px!important;column-gap:14px!important}
  .person-card .person-avatar{width:54px!important;height:54px!important;grid-column:1!important;grid-row:1/3!important}
  .person-card h3{grid-column:2!important;grid-row:1!important;font-size:1rem!important}
  .person-card p{grid-column:2!important;grid-row:2!important;font-size:.84rem!important}
  .person-card .person-no{display:none!important}
}


/* ARIO SIGNATURE 2026 — unified editorial system */
:root{--ario-ink:#14243d;--ario-muted:#687991;--ario-blue:#7897cf;--ario-ice:#dce7f8;--ario-gold:#c6ad7d}
[data-reveal]{opacity:1!important;transform:none!important}
.editorial-inner{padding-bottom:110px!important}
.editorial-inner .inner-hero{height:570px!important;border-radius:34px 34px 34px 8px!important;box-shadow:0 28px 75px rgba(0,0,0,.22)!important}
.editorial-inner .inner-hero-copy{max-width:850px!important}
.editorial-inner .inner-hero-copy h1{font-size:clamp(3.2rem,7vw,6.7rem)!important;letter-spacing:-2px!important}
.editorial-inner .inner-hero-copy h1 em{color:#c8d7f4!important;font-style:normal}
.editorial-inner .inner-hero-copy p{max-width:620px!important;font-size:1.05rem!important;line-height:2.1!important;color:#e0e7f2!important}
.editorial-inner .inner-hero-overlay{background:linear-gradient(0deg,rgba(5,13,25,.93),rgba(5,13,25,.08) 85%),linear-gradient(90deg,rgba(5,13,25,.45),transparent)!important}
.editorial-inner .section-eyebrow{color:#c1d1ef!important;letter-spacing:2px!important}
.editorial-inner .story-layout{padding:100px 0 75px!important}
.editorial-inner .story-side h2{color:#f5f7fb!important;font-size:clamp(2.7rem,4.7vw,4.1rem)!important}
.editorial-inner .story-main{border-right:1px solid rgba(180,199,230,.2)!important;color:#b8c5d8!important}
.editorial-inner .story-main .story-lead{color:#f0f4fb!important;font-size:1.45rem!important}
.editorial-inner .values-row{border-color:rgba(180,199,230,.2)!important}
.editorial-inner .values-row article{border-color:rgba(180,199,230,.16)!important}
.editorial-inner .values-row h3{color:#f1f5fc!important}
.editorial-inner .values-row p{color:#b4c1d4!important}
.staff-list,.experience-list,.journal-list{width:min(1120px,calc(100% - 50px));margin:0 auto;display:flex;flex-direction:column;gap:15px}
.staff-row{
 display:grid;grid-template-columns:76px minmax(0,1fr) auto;align-items:center;gap:24px;
 padding:25px 30px;border-radius:25px 25px 25px 8px;
 border:1px solid rgba(183,202,235,.18);
 background:linear-gradient(105deg,rgba(25,45,72,.96),rgba(14,29,50,.96));
 box-shadow:0 14px 38px rgba(0,0,0,.15);transition:transform .25s,border-color .25s,box-shadow .25s
}
.staff-row:hover,.experience-row:hover,.journal-row:hover{transform:translateY(-4px);border-color:rgba(174,198,240,.48);box-shadow:0 20px 45px rgba(0,0,0,.2)}
.staff-row-icon,.experience-icon{width:66px;height:66px;display:grid;place-items:center;border-radius:21px 21px 21px 6px;background:linear-gradient(145deg,rgba(139,168,220,.2),rgba(139,168,220,.07));border:1px solid rgba(185,205,240,.2);color:#c5d5f4;font-size:1.45rem}
.staff-row-copy h3,.experience-copy h3,.journal-copy h3{font-size:1.28rem;color:#f3f6fc;margin:0 0 7px}
.staff-row-copy p,.experience-copy p,.journal-copy p{font-size:.94rem;line-height:2;color:#b8c6d9;margin:0}
.staff-row-mark{font-size:.68rem;letter-spacing:2px;color:#9fb4d9}
.experience-row,.journal-row{
 display:grid;grid-template-columns:245px minmax(0,1fr) 58px;align-items:center;gap:28px;
 padding:16px;border-radius:26px 26px 26px 8px;
 border:1px solid rgba(183,202,235,.17);
 background:linear-gradient(105deg,rgba(25,45,72,.94),rgba(14,29,50,.94));
 box-shadow:0 14px 38px rgba(0,0,0,.13);transition:.25s
}
.experience-photo,.journal-photo{height:165px;border-radius:19px 19px 19px 6px;background-size:cover;background-position:center;filter:saturate(.82)}
.experience-copy>span,.journal-date{display:block;color:#a9bee5;font-size:.72rem;letter-spacing:1px;margin-bottom:12px}
.experience-icon,.journal-arrow{width:50px;height:50px;font-size:1rem}
.journal-row{grid-template-columns:245px minmax(0,1fr) 50px}
.journal-copy .news-date{display:block;margin-bottom:12px;color:#a9bee5}
.journal-arrow{display:grid;place-items:center;color:#c5d5f4;border:1px solid rgba(185,205,240,.18);border-radius:50%}
.contact-editorial-grid{width:min(1120px,calc(100% - 50px));margin:0 auto;display:grid;grid-template-columns:1fr 1fr;gap:18px}
.contact-editorial-item{min-height:250px;padding:34px;border:1px solid rgba(183,202,235,.18);border-radius:26px 26px 26px 8px;background:linear-gradient(145deg,#192d49,#101f35);box-shadow:0 15px 40px rgba(0,0,0,.14)}
.contact-editorial-item>span{display:block;color:#a9bee5;font-size:.7rem;letter-spacing:1.8px;margin-bottom:22px}
.contact-editorial-item>i{color:#c4d4f3;font-size:1.45rem;margin-bottom:16px}
.contact-editorial-item h3{color:#f2f5fb;font-size:1.25rem;margin-bottom:9px}
.contact-editorial-item p{color:#b9c6d8;line-height:2}
.contact-editorial-item a{display:inline-block;color:#c5d5f4;text-decoration:none;margin-top:15px}
body[data-theme="light"]{background:radial-gradient(ellipse at 12% 8%,rgba(125,157,213,.15),transparent 32%),linear-gradient(145deg,#f8faff,#edf2fa 58%,#f8faff)!important;color:#1d2d48!important}
body[data-theme="light"] .editorial-inner .story-side h2{color:#20324f!important}
body[data-theme="light"] .editorial-inner .story-main{color:#586b87!important;border-color:#d7e0ee!important}
body[data-theme="light"] .editorial-inner .story-main .story-lead{color:#253957!important}
body[data-theme="light"] .editorial-inner .values-row,body[data-theme="light"] .editorial-inner .values-row article{border-color:#d9e2ef!important}
body[data-theme="light"] .editorial-inner .values-row h3{color:#263a59!important}
body[data-theme="light"] .editorial-inner .values-row p{color:#64748b!important}
body[data-theme="light"] .staff-row,body[data-theme="light"] .experience-row,body[data-theme="light"] .journal-row,body[data-theme="light"] .contact-editorial-item{
 background:linear-gradient(120deg,#fff,#f1f5fc)!important;border-color:#dce5f1!important;box-shadow:0 12px 32px rgba(42,63,99,.07)!important
}
body[data-theme="light"] .staff-row-copy h3,body[data-theme="light"] .experience-copy h3,body[data-theme="light"] .journal-copy h3,body[data-theme="light"] .contact-editorial-item h3{color:#203451!important}
body[data-theme="light"] .staff-row-copy p,body[data-theme="light"] .experience-copy p,body[data-theme="light"] .journal-copy p,body[data-theme="light"] .contact-editorial-item p{color:#61728b!important}
body[data-theme="light"] .staff-row-mark,body[data-theme="light"] .experience-copy>span,body[data-theme="light"] .journal-copy .news-date,body[data-theme="light"] .contact-editorial-item>span{color:#627eae!important}
body[data-theme="light"] .staff-row-icon,body[data-theme="light"] .experience-icon{background:#eaf0fb;border-color:#d8e2f2;color:#4e6c9e}
body[data-theme="light"] .journal-arrow{color:#4e6c9e;border-color:#d8e2f2}

/* Authentication screen: light mode changes the WHOLE canvas, not just the form */
body[data-theme="light"]{
 --white:#203451!important;--muted:#657791!important;
 background:radial-gradient(ellipse at 10% 15%,rgba(139,169,220,.23),transparent 34%),radial-gradient(ellipse at 90% 85%,rgba(180,199,231,.22),transparent 34%),linear-gradient(135deg,#f8faff,#eaf0f9 55%,#f7faff)!important;
 color:#203451!important
}
body[data-theme="light"]:before{opacity:.42!important;background-image:linear-gradient(rgba(60,86,128,.045) 1px,transparent 1px),linear-gradient(90deg,rgba(60,86,128,.045) 1px,transparent 1px)!important}
body[data-theme="light"] .ambient.a{background:radial-gradient(circle,rgba(108,145,205,.18),transparent 68%)!important}
body[data-theme="light"] .ambient.b{background:radial-gradient(circle,rgba(150,174,216,.2),transparent 68%)!important}
body[data-theme="light"] .intro:before{
 background:linear-gradient(90deg,rgba(246,249,255,.96),rgba(246,249,255,.88) 60%,rgba(246,249,255,.55)),url('https://images.unsplash.com/photo-1498243691581-b145c3f54a5a?auto=format&fit=crop&w=1400&q=90') center/cover!important;
 opacity:1!important;box-shadow:0 25px 70px rgba(40,62,101,.1)!important;border:1px solid rgba(133,157,196,.18)!important
}
body[data-theme="light"] .intro h1{color:#1c3152!important}
body[data-theme="light"] .intro h1 span{background:linear-gradient(100deg,#47699f,#7896c8,#536f9f)!important;-webkit-background-clip:text!important;background-clip:text!important;color:transparent!important}
body[data-theme="light"] .intro-copy{color:#526783!important}
body[data-theme="light"] .feature{color:#405675!important;background:rgba(255,255,255,.68)!important;border-color:rgba(116,142,184,.22)!important}
body[data-theme="light"] .feature i{color:#5879ad!important}
body[data-theme="light"] .visual-card{background:rgba(255,255,255,.72)!important;border-color:rgba(123,148,189,.24)!important;box-shadow:0 12px 35px rgba(39,61,99,.07)!important}
body[data-theme="light"] .visual-card strong{color:#263d60!important}
body[data-theme="light"] .visual-card p{color:#60748f!important}
body[data-theme="light"] .visual-icon{color:#49699e!important;background:linear-gradient(145deg,#e6edfa,#f6f8fd)!important}
body[data-theme="light"] .topbar{background:rgba(255,255,255,.72)!important;border-color:rgba(125,149,187,.23)!important;box-shadow:0 16px 45px rgba(38,59,95,.08)!important}
body[data-theme="light"] .topbar-caption{color:#425a7d!important}
body[data-theme="light"] .brand,body[data-theme="light"] .brand-name{color:#203451!important}
body[data-theme="light"] .brand-name small{color:#70819b!important}
body[data-theme="light"] .auth-card{background:rgba(255,255,255,.83)!important;border-color:rgba(255,255,255,.95)!important;box-shadow:0 28px 75px rgba(43,64,101,.13)!important}
body[data-theme="light"] .card-heading h2{color:#203451!important}
body[data-theme="light"] .card-heading p{color:#6a7b94!important}
body[data-theme="light"] .field-label{color:#425a7d!important}
body[data-theme="light"] .input-shell input{background:#f8faff!important;color:#203451!important;border-color:#dce5f1!important}
body[data-theme="light"] .input-shell input::placeholder{color:#9aa9bd!important}
body[data-theme="light"] .secure-note,body[data-theme="light"] .bottom-note{color:#71819a!important}
body[data-theme="light"] .tabs{background:#edf2fa!important}
body[data-theme="light"] .tab{color:#687b96!important}
body[data-theme="light"] .tab.active{color:#203451!important;background:#fff!important;box-shadow:0 3px 12px rgba(44,65,103,.08)!important}
body[data-theme="light"] .submit-btn{background:linear-gradient(110deg,#506fA8,#7897c9)!important;color:#fff!important}
body[data-theme="light"] .login-topbar{background:rgba(255,255,255,.72)!important;border-color:rgba(125,149,187,.23)!important}

/* Admin console — premium dashboard skin without changing its working forms/routes */
.admin-section{border:1px solid rgba(164,188,225,.2)!important;border-radius:25px 25px 25px 8px!important;padding:28px!important;margin:22px 0!important;background:linear-gradient(145deg,rgba(22,41,66,.96),rgba(12,26,45,.96))!important;box-shadow:0 18px 48px rgba(0,0,0,.17)!important}
.admin-section h3{color:#e8effb!important;font-size:1.15rem!important;padding-bottom:16px;border-bottom:1px solid rgba(171,193,228,.15);margin-bottom:20px!important}
.admin-section h3 i{color:#adc4ed!important;margin-left:9px}
.admin-form input,.admin-form textarea,.admin-form select,.admin-section input,.admin-section textarea,.admin-section select{background:rgba(5,17,33,.65)!important;color:#e9eff9!important;border:1px solid rgba(174,197,232,.22)!important;border-radius:13px!important;padding:13px 15px!important}
.admin-section input::placeholder,.admin-section textarea::placeholder{color:#8193ad!important}
.admin-section button,.admin-section .btn-success,.admin-section .btn-warning,.admin-section .btn-danger{border-radius:12px!important;padding:11px 17px!important;font-weight:700!important}
.admin-list-item{background:rgba(255,255,255,.045)!important;border:1px solid rgba(174,197,232,.14)!important;border-radius:15px!important;padding:14px 16px!important;margin:9px 0!important;color:#dce6f5!important}
.admin-list-item strong{color:#f0f4fb!important}
body[data-theme="light"] .admin-section{background:linear-gradient(145deg,#fff,#f1f5fc)!important;border-color:#dce5f1!important;box-shadow:0 16px 40px rgba(40,62,99,.07)!important}
body[data-theme="light"] .admin-section h3{color:#243a5c!important;border-color:#e1e8f2!important}
body[data-theme="light"] .admin-section input,body[data-theme="light"] .admin-section textarea,body[data-theme="light"] .admin-section select{background:#f8faff!important;color:#263b5b!important;border-color:#dce5f1!important}
body[data-theme="light"] .admin-list-item{background:#f8faff!important;border-color:#e0e7f1!important;color:#5a6d88!important}
body[data-theme="light"] .admin-list-item strong{color:#263b5b!important}
@media(max-width:760px){
 .editorial-inner .inner-hero{height:470px!important;border-radius:24px 24px 24px 7px!important}
 .editorial-inner .story-layout{grid-template-columns:1fr!important;gap:25px!important;padding:65px 0 45px!important}
 .editorial-inner .story-main{padding-right:20px!important}
 .staff-list,.experience-list,.journal-list,.contact-editorial-grid{width:calc(100% - 30px)!important}
 .staff-row{grid-template-columns:55px minmax(0,1fr)!important;gap:15px!important;padding:18px!important}
 .staff-row-icon{width:52px;height:52px;font-size:1.1rem}
 .staff-row-mark{display:none}
 .experience-row,.journal-row{grid-template-columns:95px minmax(0,1fr)!important;gap:15px!important;padding:12px!important}
 .experience-photo,.journal-photo{height:115px}
 .experience-icon,.journal-arrow{display:none}
 .contact-editorial-grid{grid-template-columns:1fr!important}
}


.admin-kpi-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin:18px 0 28px}
.admin-kpi-grid article{padding:22px 24px;border-radius:20px 20px 20px 7px;background:linear-gradient(145deg,#1b3556,#10223b);border:1px solid rgba(177,199,235,.2);box-shadow:0 12px 32px rgba(0,0,0,.13)}
.admin-kpi-grid span,.admin-kpi-grid small{display:block;color:#aebfda;font-size:.78rem}
.admin-kpi-grid strong{display:block;color:#f3f6fc;font-size:2.1rem;line-height:1.5}
.admin-kpi-grid small{color:#8298b8}
body[data-theme="light"] .admin-kpi-grid article{background:linear-gradient(145deg,#fff,#edf3fc);border-color:#dce5f1}
body[data-theme="light"] .admin-kpi-grid span{color:#5d7190}
body[data-theme="light"] .admin-kpi-grid strong{color:#263d61}
body[data-theme="light"] .admin-kpi-grid small{color:#788aa5}
@media(max-width:760px){.admin-kpi-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.admin-kpi-grid article{padding:17px}}


.language-toggle{border:1px solid rgba(117,166,230,.42);background:rgba(85,145,220,.12);color:inherit;
padding:9px 15px;border-radius:12px;font-size:.82rem;font-weight:800;cursor:pointer;white-space:nowrap;
transition:.22s}
.language-toggle:hover{background:rgba(85,145,220,.22);transform:translateY(-1px)}
.login-topbar-actions{display:flex;align-items:center;gap:10px}
html[lang="en"] body{direction:ltr}
html[lang="en"] .page,html[lang="en"] .intro,html[lang="en"] .auth-card{text-align:left}
html[lang="en"] .intro{padding:34px 0 34px 30px}
html[lang="en"] .intro:before{inset:-30px -80px -30px -45px;background-position:center}
html[lang="en"] .feature-row{justify-content:flex-start}
html[lang="en"] .input-shell input{text-align:left}
html[lang="en"] .field-label{text-align:left}
html[lang="en"] .secure-note,html[lang="en"] .bottom-note{text-align:center}
html[lang="en"] header{direction:ltr}
html[lang="en"] nav{direction:ltr}
html[lang="en"] .container,html[lang="en"] .inner-page{direction:ltr;text-align:left}
html[lang="en"] .story-layout{direction:ltr}
html[lang="en"] .story-side,html[lang="en"] .story-main{text-align:left}
html[lang="en"] .inner-hero-copy{text-align:left}
html[lang="en"] .grid-cards,html[lang="en"] .staff-list,html[lang="en"] .experience-list,html[lang="en"] .journal-list{direction:ltr}
@media(max-width:760px){.login-topbar-actions{gap:6px}.language-toggle{padding:8px 10px;font-size:.76rem}}


html[lang="en"] body, html[lang="en"] body * {
  font-family: Inter, "Segoe UI", Arial, sans-serif !important;
}
html[lang="en"] body { direction:ltr !important; text-align:left; }
html[lang="en"] header, html[lang="en"] nav, html[lang="en"] .auth-btns,
html[lang="en"] .login-topbar-actions { direction:ltr !important; }
html[lang="en"] .container, html[lang="en"] .inner-page,
html[lang="en"] .story-layout, html[lang="en"] .editorial-inner { direction:ltr !important; }
html[lang="en"] .page-title, html[lang="en"] .hero-card { text-align:left; }
html[lang="en"] .input-shell input { text-align:left !important; direction:ltr !important; }
html[lang="en"] .input-shell>i { right:auto !important; left:16px !important; }
html[lang="en"] .input-shell input { padding:0 46px 0 48px !important; }
html[lang="en"] .reveal { left:auto !important; right:13px !important; }
html[lang="en"] .intro, html[lang="en"] .auth-card,
html[lang="en"] .inner-hero-copy, html[lang="en"] .story-main,
html[lang="en"] .story-side { text-align:left !important; }
html[lang="en"] .intro { padding:34px 0 34px 30px !important; }
html[lang="en"] .intro:before { inset:-30px -80px -30px -45px !important; }
html[lang="en"] .feature-row { justify-content:flex-start !important; }
html[lang="en"] .secure-note, html[lang="en"] .bottom-note { text-align:center !important; }
html[lang="en"] .hero-content { text-align:left !important; }
html[lang="en"] .hero-cta { justify-content:flex-start !important; }
html[lang="en"] .hero-caption { direction:ltr !important; }
html[lang="en"] .staff-list, html[lang="en"] .experience-list,
html[lang="en"] .journal-list, html[lang="en"] .contact-editorial-grid { direction:ltr !important; }
html[lang="en"] .admin-list-item, html[lang="en"] .admin-form { direction:ltr !important; }
html[lang="en"] .admin-section h3 { text-align:left !important; }
html[lang="en"] .login-topbar-actions { margin-left:auto; }
.language-toggle { min-width:78px; }

</style>
</head>
<body>
    <header>
        <div class="logo-container">
            <div class="logo-box">آ</div>
            <div class="logo-text">آریو مصلی‌نژاد<span>دولتی - ارومیه</span></div>
        </div>
        <nav>
            <a href="/home" class="{{ 'active' if active_page == 'home' else '' }}">خانه</a>
            <a href="/about" class="{{ 'active' if active_page == 'about' else '' }}">درباره ما</a>
            <a href="/staff" class="{{ 'active' if active_page == 'staff' else '' }}">کادر مدرسه</a>
            <a href="/activities" class="{{ 'active' if active_page == 'activities' else '' }}">فعالیت‌ها</a>
            <a href="/news" class="{{ 'active' if active_page == 'news' else '' }}">اخبار</a>
            <a href="/contact" class="{{ 'active' if active_page == 'contact' else '' }}">تماس</a>
            {% if session.get('role') in ["مدیر سایت (شما)", "مدیر مدرسه"] %}
                <a href="/admin" class="{{ 'active' if active_page == 'admin' else '' }}" style="color: #d97706; font-weight: 700;">پنل مدیریت</a>
            {% endif %}
        </nav>
        <div class="auth-btns login-topbar-actions">
            <button class="language-toggle" type="button" data-language-toggle onclick="toggleArioLanguage()">English</button>
            <button class="theme-toggle" type="button" data-theme-toggle onclick="toggleArioTheme()"><i class="fa-solid fa-sun"></i><span>حالت روشن</span></button>
            {% if session.get('username') %}
                <span style="font-size: 0.8rem; color: #64748b; align-self: center; margin-left: 10px;">{{ session.get('role') }}</span>
                <a href="/logout" class="btn-outline" style="color: #ef4444; border-color: #ef4444;">خروج</a>
            {% else %}
                <a href="/" class="btn-outline">ورود</a>
            {% endif %}
        </div>
    </header>
    {% block content %}{% endblock %}
    <footer><strong>آریو مصلی‌نژاد</strong> · جایی برای یادگیری، تجربه و ساختن آینده</footer>

<script>
(function () {
    const key = 'ario-signature-theme-v2';
    function applyTheme(theme) {
        document.body.setAttribute('data-theme', theme);
        document.querySelectorAll('[data-theme-toggle]').forEach(function (button) {
            const light = theme === 'light';
            button.innerHTML = light
                ? '<span class="theme-icon"><i class="fa-solid fa-moon"></i></span><span class="theme-label">پوسته تیره</span><span class="theme-track"><span></span></span>'
                : '<span class="theme-icon"><i class="fa-solid fa-sun"></i></span><span class="theme-label">پوسته روشن</span><span class="theme-track"><span></span></span>';
            button.setAttribute('aria-label', light ? 'فعال‌کردن حالت تیره' : 'فعال‌کردن حالت روشن');
            button.setAttribute('title', light ? 'فعال‌کردن حالت تیره' : 'فعال‌کردن حالت روشن');
        });
    }
    window.toggleArioTheme = function () {
        const next = document.body.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
        try { localStorage.setItem(key, next); } catch (e) {}
        applyTheme(next);
    };
    let saved = 'dark';
    try { saved = localStorage.getItem(key) || 'dark'; } catch (e) {}
    applyTheme(saved);
    document.addEventListener('DOMContentLoaded', function () { applyTheme(saved); });
})();
</script>


<script>
(function(){
  const items = document.querySelectorAll('[data-reveal]');
  if (!('IntersectionObserver' in window) || window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    items.forEach(el => el.classList.add('is-visible')); return;
  }
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if(entry.isIntersecting){ entry.target.classList.add('is-visible'); observer.unobserve(entry.target); }
    });
  }, {threshold:.12});
  items.forEach(el => observer.observe(el));
})();
</script>


<script>
(function () {
  const dictionary = {
    "مدرسه آریو مصلی‌نژاد": "Ario Mosallinejad School",
    "آریو مصلی‌نژاد": "Ario Mosallinejad",
    "دولتی - ارومیه": "Public School · Urmia",
    "مدرسه آریو مصلی‌نژاد | {{ title }}": "Ario Mosallinejad School | {{ title }}",
    "ورود به آریو | مدرسه آریو مصلی‌نژاد": "Sign in to Ario | Ario Mosallinejad School",
    "آ": "A",
    "خانه": "Home",
    "درباره ما": "About Us",
    "کادر مدرسه": "Our Team",
    "فعالیت‌ها": "Activities",
    "اخبار": "News",
    "تماس": "Contact",
    "تماس با ما": "Contact Us",
    "پنل مدیریت": "Admin Panel",
    "پنل مدیریت پیشرفته": "Advanced Admin Panel",
    "حالت روشن": "Light Mode",
    "حالت تیره": "Dark Mode",
    "پوسته روشن": "Light Theme",
    "پوسته تیره": "Dark Theme",
    "خروج": "Log Out",
    "ورود": "Sign In",
    "مدیر سایت (شما)": "Website Administrator",
    "مدیر مدرسه": "School Principal",
    "معلم": "Teacher",
    "دانش‌آموز": "Student",
    "اصلی": "Primary",
    "ویرایش": "Edit",
    "حذف": "Delete",
    "افزودن": "Add",
    "انصراف": "Cancel",
    "ثبت ویرایش": "Save Changes",
    "ذخیره متون": "Save Text",
    "ذخیره و انتشار خبر": "Save & Publish News",
    "افزودن کاربر": "Add User",
    "آمار مدرسه": "School Statistics",
    "فضای اختصاصی مدرسه آریو مصلی‌نژاد": "Ario School Private Portal",
    "به فضای یادگیری آریو خوش آمدید": "Welcome to Ario's Learning Community",
    "آینده از همین‌جا": "The Future",
    "شروع می‌شود.": "Starts Here.",
    "اینجا نقطه اتصال ایده‌ها، تلاش‌ها و اتفاق‌های خوب مدرسه آریو مصلی‌نژاد است.": "A place where ideas, effort, and memorable moments come together at Ario School.",
    "وارد حساب خود شوید و همراه جامعه مدرسه، قدم بعدی را بسازید.": "Sign in and take your next step with the Ario community.",
    "فضای امن و اختصاصی": "A Safe, Dedicated Space",
    "دسترسی سریع و ساده": "Quick and Easy Access",
    "همراه مسیر رشد": "Here for Every Step of Growth",
    "هر روز، یک فرصت تازه برای درخشیدن": "Every Day Is a New Chance to Shine",
    "با هم یاد می‌گیریم، تجربه می‌کنیم و آینده‌ای بهتر می‌سازیم.": "We learn, explore, and build a better future together.",
    "سامانه یکپارچه مدرسه": "Integrated School Platform",
    "اینجا شروعِ اتفاق‌های بزرگه ✨": "Great Things Start Here ✨",
    "برای ادامه مسیر، وارد حساب کاربری‌ات شو یا حساب جدید بساز.": "Sign in to continue, or create a new account.",
    "ورود به حساب": "Sign In",
    "ایجاد حساب": "Create Account",
    "نام کاربری": "Username",
    "نام کاربری دلخواه": "Choose a Username",
    "رمز عبور": "Password",
    "ورود به سامانه": "Sign In",
    "نام کاربری جدید": "New Username",
    "ساخت حساب کاربری": "Create Account",
    "اطلاعات حساب شما در محیطی امن نگهداری می‌شود": "Your account information is stored securely.",
    "© مدرسه آریو مصلی‌نژاد · با افتخار برای جامعه مدرسه": "© Ario Mosallinejad School · Made with pride for our school community",
    "· جایی برای یادگیری، تجربه و ساختن آینده": "· A place to learn, explore, and shape the future",
    "آینده را با هم می‌سازیم.": "We Build the Future Together.",
    "اینجا ایده‌ها جان می‌گیرند و قدم‌های کوچک، آینده را می‌سازند.": "Ideas come to life here, and small steps shape the future.",
    "اینجا، آریو": "This Is Where",
    "زندگی می‌کند.": "Ario Comes to Life.",
    "آریو، فراتر از کلاس درس": "Ario Is More Than a Classroom",
    "در آریو، هر پرسش دریچه‌ای تازه است؛ با تجربه کردن، همکاری و کشف استعدادها، برای ساختن فردایی روشن‌تر آماده می‌شویم.": "At Ario, every question opens a new door. Through hands-on learning, teamwork, and discovering our talents, we prepare to shape a brighter tomorrow.",
    "عضو معرفی‌شده کادر": "Team Members",
    "فعالیت دانش‌آموزی": "Student Activities",
    "خبر و رویداد": "News & Events",
    "یادگیری · دوستی · کشف": "LEARNING · FRIENDSHIP · DISCOVERY",
    "تجربه‌های آریو": "Explore Ario",
    "داستان ما": "Our Story",
    "اینجا فرصت داریم کنجکاوی کنیم، مهارت‌های تازه بیاموزیم، دوستی بسازیم و توانایی‌هایمان را به دستاورد تبدیل کنیم.": "Here, we ask questions, learn new skills, build friendships, and turn our potential into meaningful achievements.",
    "کنجکاوی،": "Curiosity",
    "شروعِ هر اتفاق بزرگ است.": "Is Where Great Things Begin.",
    "یادگیری واقعی با یک پرسش آغاز می‌شود؛ با ایده‌پردازی، تجربه و همکاری ادامه پیدا می‌کند و به ساختن راه‌های تازه می‌رسد.": "Real learning begins with a question. It grows through ideas, experience, and teamwork—and leads to new possibilities.",
    "بیشتر درباره فعالیت‌ها": "Discover Our Activities",
    "هر روز، یک قدم به سوی آینده‌ای بهتر.": "Every Day, One Step Toward a Brighter Future.",
    "با مدرسه در ارتباط باش": "Connect With Our School",
    "یک مدرسه؛": "One School;",
    "هزاران امکان.": "A Thousand Possibilities.",
    "داستان ما درباره رشد، رفاقت و ساختن فردایی روشن‌تر است.": "Our story is about growth, friendship, and creating a brighter tomorrow.",
    "آریو را": "Discover",
    "بشناس.": "Ario.",
    "مدرسه، فقط یک ساختمان و چند کلاس نیست؛ جایی است که شخصیت، رویا و آینده شکل می‌گیرد.": "A school is more than a building and classrooms; it is where character, dreams, and futures take shape.",
    "ما باور داریم هر دانش‌آموز استعداد و مسیر منحصربه‌فرد خودش را دارد. وظیفه ما فراهم کردن فضایی امن، پویا و الهام‌بخش برای کشف این توانایی‌هاست.": "We believe every student has unique talents and a path of their own. Our mission is to create a safe, vibrant, and inspiring environment where those abilities can flourish.",
    "برای پرسیدن، کشف کردن و پیدا کردن پاسخ‌های تازه.": "To ask questions, explore, and find new answers.",
    "رشد در کنار یکدیگر و یاد گرفتن از تفاوت‌ها.": "Growing together and learning from our differences.",
    "قدم‌های کوچک و پیوسته برای ساختن آینده‌ای بهتر.": "Small, consistent steps toward a better future.",
    "کنجکاوی": "Curiosity",
    "همراهی": "Togetherness",
    "پیشرفت": "Progress",
    "آدم‌های": "The People",
    "اثرگذار": "Who Make a Difference",
    "آریو.": "At Ario.",
    "یک تیم؛": "One Team;",
    "یک مسیر.": "One Journey.",
    "آدم‌هایی که هر روز با دانش، تعهد و همراهی، مسیر رشد را روشن‌تر می‌کنند.": "People who bring knowledge, commitment, and care to make every student's path brighter.",
    "OUR COMMUNITY": "OUR COMMUNITY",
    "پشت هر تجربه خوب در مدرسه، آدم‌هایی هستند که با عشق و مسئولیت کار می‌کنند.": "Behind every meaningful school experience are people who work with care and responsibility.",
    "کادر آریو همراه دانش‌آموزان است تا فضایی امن، پویا و الهام‌بخش برای یادگیری و شکوفایی استعدادها شکل بگیرد.": "The Ario team works alongside students to create a safe, dynamic, and inspiring environment for learning and growth.",
    "اطلاعات کادر مدرسه هنوز ثبت نشده است.": "Team information has not been added yet.",
    "کلاس درس،": "The Classroom",
    "تمام ماجرا نیست.": "Is Only the Beginning.",
    "ایده‌ها وقتی زنده می‌شوند که آن‌ها را تجربه کنیم.": "Ideas Come Alive When We Put Them Into Practice.",
    "یادگیری": "Learning",
    "در جریان است.": "In Motion.",
    "هر تجربه، فرصتی برای کشف توانایی‌های تازه است.": "Every experience is an opportunity to discover new abilities.",
    "از همکاری و هنر تا فناوری و فعالیت‌های گروهی؛ آریو یادگیری را به تجربه‌ای زنده و ماندگار تبدیل می‌کند.": "From teamwork and the arts to technology and group projects, Ario turns learning into a meaningful, lasting experience.",
    "تجربه آریو": "The Ario Experience",
    "هنوز فعالیتی ثبت نشده است.": "No activities have been added yet.",
    "روایت روزهای": "Stories From",
    "پر اتفاق آریو.": "Life at Ario.",
    "خبرها، لحظه‌ها و اتفاق‌هایی که ارزش به خاطر سپردن دارند.": "News, moments, and events worth remembering.",
    "خبرهای": "School",
    "مدرسه.": "News.",
    "هر روز در آریو داستانی تازه برای گفتن وجود دارد.": "Every day at Ario brings a new story to tell.",
    "اینجا می‌توانید خبرها، رویدادها و لحظه‌های مهم جامعه مدرسه را دنبال کنید.": "Follow the latest news, events, and important moments from our school community.",
    "خبر مدرسه": "School News",
    "هنوز خبری منتشر نشده است. به‌زودی اینجا پر از خبرهای تازه می‌شود.": "No news has been published yet. Check back soon for updates.",
    "راه‌های": "Ways to",
    "ارتباط": "Connect",
    "با ما.": "With Us.",
    "برای پرسش، پیشنهاد یا آشنایی بیشتر، خوشحال می‌شویم صدایتان را بشنویم.": "For questions, suggestions, or to learn more, we would be happy to hear from you.",
    "با ما": "Get in",
    "در تماس باش.": "Touch.",
    "ارتباط خوب، شروع یک همکاری ارزشمند است.": "Good communication is the beginning of a valuable partnership.",
    "برای دریافت راهنمایی یا مطرح‌کردن پرسش‌هایتان، از راه‌های زیر با مدرسه آریو در ارتباط باشید.": "For assistance or questions, contact Ario School using the details below.",
    "آدرس مدرسه": "School Address",
    "ارومیه، محله بزرگباش، اول خیابان جانبازان": "Janbazan Street, Bozorgbash, Urmia, Iran",
    "تلفن تماس": "Phone",
    "باز کردن در نقشه": "Open in Maps",
    "مدیریت تمام بخش‌های سایت بدون نیاز به کدنویسی": "Manage every part of the website without coding.",
    "کاربران سامانه": "Platform Users",
    "حساب‌های ثبت‌شده": "Registered Accounts",
    "اعضای کادر": "Team Members",
    "معرفی‌شده در سایت": "Featured on the Website",
    "فعالیت‌ها": "Activities",
    "تجربه‌های مدرسه": "School Experiences",
    "خبرها": "News",
    "مطالب منتشرشده": "Published Posts",
    "مدیریت کاربران (ادمین‌ها و معلم‌ها)": "User Management (Administrators & Teachers)",
    "عنوان بزرگ صفحه خانه": "Homepage Main Heading",
    "متن زیر عنوان صفحه خانه": "Homepage Subtitle",
    "متن صفحه درباره ما": "About Us Page Text",
    "ویرایش متن‌های اصلی": "Edit Main Website Text",
    "انتشار خبر جدید": "Publish a News Article",
    "خبر پس از ذخیره در صفحه «اخبار» نمایش داده می‌شود و با خروج از حساب حذف نخواهد شد.": "After saving, this article will appear on the News page and will remain published after you log out.",
    "افزودن کارت جدید به هر بخش": "Add a New Card to Any Section",
    "صفحه خانه": "Home Page",
    "عنوان": "Title",
    "توضیحات": "Description",
    "مدیر": "Principal",
    "معاون": "Deputy",
    "ستاره": "Star",
    "کامپیوتر": "Computer",
    "کتاب": "Book",
    "مدرسه": "School",
    "جام": "Trophy",
    "در حال ویرایش کارت: {{ edit_card.title }}": "Editing card: {{ edit_card.title }}",
    "لیست تمام کارت‌ها": "All Cards",
    "صفحه خانه (Home)": "Home Page",
    "کادر مدرسه (Staff)": "School Team",
    "فعالیت‌ها (Activities)": "Activities",
    "اخبار (News)": "News",
    "نام کاربری خود را وارد کنید": "Enter your username",
    "یک نام کاربری انتخاب کنید": "Choose a username",
    "یک رمز عبور بسازید": "Create a password",
    "عنوان خبر": "News Title",
    "متن خبر": "News Content",
    "تاریخ خبر (اختیاری؛ مثلاً ۱۴۰۵/۰۸/۲۹)": "News Date (Optional, e.g. 2026/11/20)",
    "لینک تصویر خبر (اختیاری)": "News Image URL (Optional)",
    "متن کامل خبر را بنویسید...": "Write the full news article...",
    "توضیحات": "Description",
    "این کارت حذف شود؟": "Delete this card?",
    "مطمئنی می‌خوای این کاربر رو حذف کنی؟": "Are you sure you want to delete this user?",
    "مخفی کردن رمز": "Hide password",
    "نمایش رمز": "Show password",
    "نام کاربری باید ۳ تا ۳۲ نویسه و رمز عبور حداقل ۶ نویسه باشد.": "Username must be 3–32 characters and password must be at least 6 characters.",
    "نام کاربری و رمز عبور را کامل وارد کنید.": "Please enter both your username and password.",
    "نام کاربری یا رمز عبور اشتباه است.": "Incorrect username or password.",
    "این نام کاربری قبلا وجود دارد!": "This username is already taken.",
    "ثبت‌نام موفق! حالا با همین اطلاعات وارد شوید.": "Registration successful! You can now sign in with your new account.",
    "شما دسترسی به این بخش ندارید.": "You do not have permission to access this section.",
    "بازگشت": "Go Back",
    "جناب آقای سلاطین": "Mr. Salatin",
    "جناب آقای الوانی": "Mr. Alvani",
    "مدیر مدرسه": "School Principal",
    "معاون آموزشی": "Academic Deputy",
    "گروه هنری و تئاتر": "Arts & Theatre Group",
    "اجرای نمایش‌های زیبا در مناسبت‌های مختلف.": "Performing plays and shows for special occasions.",
    "نشریه دانش‌آموزی": "Student Magazine",
    "قلم و ایده دانش‌آموزان در قالب نشریه.": "Student writing and ideas shared through a school magazine.",
    "المپیاد ورزشی": "School Sports Tournament",
    "رقابت سالم و پرشاط بین کلاس‌ها.": "Friendly and energetic competitions between classes.",
    "روز دانش‌آموز": "Student Day",
    "روز دانش‌آموز، روز تجلیل از آینده‌سازان این مرز و بوم است.": "Student Day celebrates the young people who will shape our future.",
    "ما کی هستیم": "Who We Are",
    "مدرسه دولتی پسرانه در ارومیه": "A public boys' school in Urmia",
    "طراح سایت": "Website Designers",
    "آیدی": "Social Media",
    "روش ما": "Our Approach",
    "ترکیبی از آموزش منظم، فعالیت‌های دانش‌آموزی و فضایی دوستانه برای یادگیری بهتر": "A blend of structured learning, student activities, and a friendly environment.",
    "کتابخانه": "Library",
    "فضایی آرام برای مطالعه، امانت کتاب و رشد اندیشه": "A quiet space for reading, borrowing books, and developing ideas.",
    "اینجا ایده‌ها جان می‌گیرند و قدم‌های کوچک، آینده را می‌سازند.": "Ideas come to life here, and small steps shape the future.",
    "ما یک مدرسه نیستیم؛ یک تیمیم. تیمی برای یادگیری و رشد.": "We are more than a school; we are a team dedicated to learning and growth.",
    "جایی که درس، ایده و حال خوب کنار هم می‌نشینند.": "Where learning, ideas, and positive energy come together.",
    "آینده‌سازان این مرز و بوم": "the future generation",
    "آریو مصلی‌نژاد، خانه یادگیری، دوستی و ساختن آینده است.": "Ario Mosallinejad is a home for learning, friendship, and building the future.",
    "آریو مصلی‌نژاد فقط یک اسم روی سربرگ نیست. یک مدرسه دولتی پسرانه در ارومیه است که با مدیریت دلسوزانه آقای سلاطین و تلاش کادر مجرب، محیطی امن و پویا برای آینده‌سازان این مرز و بوم فراهم کرده است.": "Ario Mosallinejad is more than a name on a letterhead. It is a public boys' school in Urmia, providing a safe and supportive environment through dedicated leadership and the commitment of its experienced staff.",
    'معاون آموزشی': 'Academic Deputy',
    'محمد امین سعیدی و امیرعباس قاسمی': 'Mohammad Amin Saeedi and Amirabbas Ghasemi',
    'مدرسه دولتی پسرانه در ارومیه': "A public boys' school in Urmia",
    'ترکیبی از آموزش منظم، فعالیت\u200cهای دانش\u200cآموزی و فضایی دوستانه برای یادگیری بهتر': 'A blend of structured learning, student activities, and a friendly environment.',
    'فضایی آرام برای مطالعه، امانت کتاب و رشد اندیشه': 'A quiet space for reading, borrowing books, and developing ideas.',
    'متون با موفقیت ذخیره شد.': 'Text was saved successfully.',
    'عنوان و متن خبر را وارد کنید.': 'Please enter both a news title and its content.',
    'لینک تصویر معتبر نیست.': 'The image URL is not valid.',
    'خبر با موفقیت ذخیره و منتشر شد.': 'The news article was published successfully.',
    'اطلاعات کارت معتبر نیست.': 'The card information is invalid.',
    'کارت جدید اضافه شد.': 'The new card was added.',
    'کارت با موفقیت ویرایش شد.': 'The card was updated successfully.',
    'کارت حذف شد.': 'The card was deleted.',
    'نام کاربری باید ۳ تا ۳۲ نویسه و رمز حداقل ۶ نویسه باشد.': 'Username must be 3–32 characters and password must be at least 6 characters.',
    'این نام کاربری از قبل وجود دارد!': 'This username already exists.',
    'کاربر جدید با موفقیت اضافه شد.': 'The new user was added successfully.',
    'شما نمی\u200cتوانید کاربر اصلی (admin) را حذف کنید!': 'You cannot delete the primary administrator (admin).',
    'کاربر حذف شد.': 'The user was deleted.',
    'شما دسترسی به این بخش ندارید.': 'You do not have permission to access this section.',
    'پنل ادمین': 'Admin Panel',
    'جایی برای یادگیری و ساختن آینده': 'A place to learn and shape the future',
    'فضای یادگیری و مدرسه': 'A place for learning and school life',
    'آیدی': 'Social Media',
    'طراح سایت': 'Website Designers',
    'روش ما': 'Our Approach',
    'ما کی هستیم': 'Who We Are',
    'کتابخانه': 'Library',
    'روز دانش\u200cآموز': 'Student Day',
    'گروه هنری و تئاتر': 'Arts & Theatre Group',
    'نشریه دانش\u200cآموزی': 'Student Magazine',
    'المپیاد ورزشی': 'School Sports Tournament',
  };

  const attributeDictionary = {
    "نام کاربری": "Username",
    "نام کاربری جدید": "New username",
    "نام کاربری خود را وارد کنید": "Enter your username",
    "یک نام کاربری انتخاب کنید": "Choose a username",
    "رمز عبور": "Password",
    "یک رمز عبور بسازید": "Create a password",
    "عنوان خبر": "News title",
    "متن خبر": "News content",
    "تاریخ خبر (اختیاری؛ مثلاً ۱۴۰۵/۰۸/۲۹)": "News date (optional, e.g. 2026/11/20)",
    "لینک تصویر خبر (اختیاری)": "News image URL (optional)",
    "متن کامل خبر را بنویسید...": "Write the full news article...",
    "عنوان": "Title",
    "توضیحات": "Description"
  };

  const reverseDictionary = {};
  Object.keys(dictionary).forEach(key => { reverseDictionary[dictionary[key]] = key; });
  const originalNodes = new WeakMap();
  const originalAttrs = new WeakMap();

  function applyLanguage(lang) {
    const english = lang === "en";
    document.documentElement.lang = english ? "en" : "fa";
    document.documentElement.dir = english ? "ltr" : "rtl";
    document.body.dataset.language = lang;
    document.body.classList.toggle("language-english", english);

    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);

    nodes.forEach(node => {
      if (!originalNodes.has(node)) originalNodes.set(node, node.nodeValue);
      const original = originalNodes.get(node);
      const key = original.trim();
      if (!key) return;
      const translated = dictionary[key];
      if (english && translated) {
        node.nodeValue = original.replace(key, translated);
      } else if (!english) {
        node.nodeValue = original.replace(key, reverseDictionary[key] || key);
      }
    });

    document.querySelectorAll("input, textarea, select, button, a, [title], [aria-label]").forEach(el => {
      ["placeholder", "title", "aria-label"].forEach(attr => {
        if (!el.hasAttribute(attr)) return;
        let saved = originalAttrs.get(el);
        if (!saved) { saved = {}; originalAttrs.set(el, saved); }
        if (saved[attr] === undefined) saved[attr] = el.getAttribute(attr);
        const original = saved[attr];
        if (english) el.setAttribute(attr, attributeDictionary[original] || dictionary[original] || original);
        else el.setAttribute(attr, original);
      });
      if (el.tagName === "OPTION" && el.textContent.trim()) {
        if (!originalAttrs.has(el)) originalAttrs.set(el, {});
        const saved = originalAttrs.get(el);
        if (saved.optionText === undefined) saved.optionText = el.textContent;
        const key = saved.optionText.trim();
        if (english && dictionary[key]) el.textContent = dictionary[key];
        if (!english) el.textContent = saved.optionText;
      }
    });

    document.querySelectorAll("[data-language-toggle]").forEach(button => {
      button.textContent = english ? "فارسی" : "English";
      button.setAttribute("aria-label", english ? "Switch to Persian" : "Switch to English");
      button.setAttribute("title", english ? "Switch to Persian" : "Switch to English");
    });

    const baseTitle = document.body.dataset.originalTitle || document.title;
    if (english) {
      document.title = baseTitle
        .replace("ورود به آریو", "Sign In to Ario")
        .replace("مدرسه آریو مصلی‌نژاد", "Ario Mosallinejad School")
        .replace("خانه", "Home")
        .replace("درباره ما", "About Us")
        .replace("کادر مدرسه", "Our Team")
        .replace("فعالیت‌ها", "Activities")
        .replace("اخبار", "News")
        .replace("تماس با ما", "Contact Us")
        .replace("پنل ادمین", "Admin Panel");
    } else {
      document.title = baseTitle;
    }
    document.body.style.direction = english ? "ltr" : "rtl";
  }

  window.toggleArioLanguage = function () {
    const next = document.documentElement.lang === "en" ? "fa" : "en";
    try { localStorage.setItem("ario-language", next); } catch (e) {}
    document.cookie = "ario-language=" + next + "; path=/; max-age=31536000; SameSite=Lax";
    applyLanguage(next);
  };

  document.addEventListener("DOMContentLoaded", function () {
    document.body.dataset.originalTitle = document.title;
    let saved = "fa";
    try { saved = localStorage.getItem("ario-language") || "fa"; } catch (e) {}
    document.cookie = "ario-language=" + saved + "; path=/; max-age=31536000; SameSite=Lax";
    applyLanguage(saved);
  });
})();
</script>

</body>
</html>
"""
# ==========================================
# صفحه ورود لاکچری (با حرکت ابرها، نور خورشید و دکمه هوشمند)
# ==========================================
AUTH_HTML = """
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="theme-color" content="#071426">
    <title>ورود به آریو | مدرسه آریو مصلی‌نژاد</title>
    <link href="https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            --bg:#071426; --panel:rgba(14,30,53,.72); --line:rgba(255,255,255,.13);
            --white:#f7faff; --muted:#9aacc5; --cyan:#55e4d2; --blue:#638bff;
        }
        * { box-sizing:border-box; margin:0; padding:0; font-family:'Vazirmatn',sans-serif; }
        body {
            min-height:100vh; min-height:100dvh; color:var(--white); overflow-x:hidden;
            background:
              radial-gradient(ellipse at 12% 15%,rgba(45,105,190,.28),transparent 34%),
              radial-gradient(ellipse at 86% 82%,rgba(28,190,170,.18),transparent 34%),
              linear-gradient(135deg,#06101f 0%,#0a1d35 52%,#071426 100%);
        }
        body:before {
            content:""; position:fixed; inset:0; pointer-events:none; opacity:.2;
            background-image:linear-gradient(rgba(255,255,255,.035) 1px,transparent 1px),
                             linear-gradient(90deg,rgba(255,255,255,.035) 1px,transparent 1px);
            background-size:54px 54px; mask-image:linear-gradient(to bottom,black,transparent 90%);
        }
        .ambient { position:fixed; border-radius:50%; filter:blur(2px); pointer-events:none; z-index:0; }
        .ambient.a { width:360px;height:360px;top:12%;right:-150px;background:radial-gradient(circle,rgba(79,132,255,.22),transparent 68%);animation:drift 12s ease-in-out infinite alternate; }
        .ambient.b { width:420px;height:420px;bottom:-190px;left:5%;background:radial-gradient(circle,rgba(47,222,193,.16),transparent 68%);animation:drift 15s ease-in-out infinite alternate-reverse; }
        @keyframes drift { to { transform:translate(35px,-25px) scale(1.12); } }
        .topbar {
            width:min(1240px,calc(100% - 64px)); margin:22px auto 0; min-height:74px;
            display:flex; align-items:center; justify-content:space-between; gap:20px;
            padding:12px 18px; border:1px solid rgba(255,255,255,.13);
            border-radius:22px; background:rgba(255,255,255,.055);
            backdrop-filter:blur(22px); -webkit-backdrop-filter:blur(22px);
            box-shadow:0 16px 45px rgba(0,0,0,.16); position:relative; z-index:2;
        }
        .brand { display:flex; align-items:center; gap:13px; text-decoration:none; color:white; }
        .brand-mark {
            width:46px;height:46px;display:grid;place-items:center;border-radius:15px;
            color:#061a2b;font-size:23px;font-weight:900;
            background:linear-gradient(145deg,#8af3e4,#62a7ff);
            box-shadow:0 8px 25px rgba(85,228,210,.22);
        }
        .brand-name { font-weight:850;font-size:1rem;letter-spacing:-.3px; }
        .brand-name small { display:block;color:#9eb1c9;font-size:.72rem;font-weight:400;margin-top:2px; }
        .top-links { display:flex;align-items:center;gap:8px; }
        .top-links a { color:#bdcbe0;text-decoration:none;padding:10px 15px;border-radius:12px;font-size:.86rem;transition:.25s; }
        .top-links a:hover { color:white;background:rgba(255,255,255,.09); }
        .top-links .home-link { border:1px solid rgba(255,255,255,.17);color:white; }
        .page {
            width:min(1280px,calc(100% - 64px)); min-height:calc(100vh - 125px);
            margin:0 auto; padding:54px 0 62px; display:grid;
            grid-template-columns:1.08fr .92fr; align-items:center; gap:clamp(35px,7vw,100px);
            position:relative; z-index:1;
        }
        .intro { padding:34px 30px 34px 0; position:relative; isolation:isolate; }
        .intro:before { content:""; position:absolute; z-index:-1; inset:-30px -45px -30px -80px; border-radius:4px; background:linear-gradient(90deg,rgba(5,13,24,.96),rgba(5,13,24,.72) 58%,rgba(5,13,24,.15)),url('https://images.unsplash.com/photo-1498243691581-b145c3f54a5a?auto=format&fit=crop&w=1400&q=90') center/cover; opacity:.92; box-shadow:0 25px 70px rgba(0,0,0,.25); }
        .eyebrow {
            display:inline-flex;align-items:center;gap:9px;padding:8px 13px;
            color:#a8f5e9;background:rgba(85,228,210,.08);
            border:1px solid rgba(85,228,210,.2);border-radius:30px;font-size:.78rem;font-weight:700;
        }
        .eyebrow i { font-size:.75rem; }
        .intro h1 { font-size:clamp(2.5rem,5.2vw,4.8rem);line-height:1.27;letter-spacing:-2px;margin:25px 0 18px;font-weight:950; }
        .intro h1 span {
            background:linear-gradient(100deg,#76f0dc 8%,#77a9ff 58%,#c5a5ff 100%);
            -webkit-background-clip:text;background-clip:text;color:transparent;
        }
        .intro-copy { max-width:550px;color:#a9bad0;font-size:1.02rem;line-height:2.15; }
        .feature-row { display:flex;gap:12px;flex-wrap:wrap;margin-top:35px; }
        .feature {
            display:flex;align-items:center;gap:10px;padding:12px 15px;
            border:1px solid rgba(255,255,255,.1);background:rgba(255,255,255,.045);
            border-radius:15px;color:#c6d3e5;font-size:.82rem;
        }
        .feature i { color:var(--cyan);font-size:1rem; }
        .visual-card {
            margin-top:42px;max-width:520px;min-height:150px;padding:22px;
            border:1px solid rgba(255,255,255,.13);border-radius:23px;
            background:linear-gradient(130deg,rgba(255,255,255,.09),rgba(255,255,255,.025));
            backdrop-filter:blur(16px);display:flex;align-items:center;gap:18px;
        }
        .visual-icon {
            flex:0 0 58px;height:58px;display:grid;place-items:center;border-radius:19px;
            background:linear-gradient(145deg,rgba(85,228,210,.2),rgba(99,139,255,.2));
            color:#8bf0e0;font-size:1.45rem;
        }
        .visual-card strong { display:block;font-size:.98rem;margin-bottom:6px; }
        .visual-card p { color:#9fb0c7;font-size:.8rem;line-height:1.9; }
        .auth-wrap { width:100%;max-width:470px;justify-self:end; }
        .auth-card {
            position:relative;overflow:hidden;padding:clamp(27px,4vw,42px);
            border-radius:30px;border:1px solid rgba(255,255,255,.18);
            background:linear-gradient(145deg,rgba(255,255,255,.13),rgba(255,255,255,.055));
            backdrop-filter:blur(28px);-webkit-backdrop-filter:blur(28px);
            box-shadow:0 35px 100px rgba(0,0,0,.36),inset 0 1px rgba(255,255,255,.12);
        }
        .auth-card:before {
            content:"";position:absolute;width:220px;height:220px;top:-150px;left:-90px;
            border-radius:50%;background:rgba(85,228,210,.17);filter:blur(10px);pointer-events:none;
        }
        .card-heading { position:relative;margin-bottom:27px; }
        .card-logo { display:flex;align-items:center;gap:12px;margin-bottom:25px; }
        .card-logo .brand-mark { width:42px;height:42px;border-radius:14px;font-size:20px; }
        .card-logo span { color:#c3d1e4;font-size:.82rem; }
        .card-heading h2 { font-size:1.75rem;font-weight:900;letter-spacing:-.6px;margin-bottom:7px; }
        .card-heading p { color:#a5b6cc;font-size:.86rem;line-height:1.9; }
        .tabs { display:grid;grid-template-columns:1fr 1fr;padding:5px;gap:5px;border-radius:15px;background:rgba(2,10,23,.36);margin-bottom:22px; }
        .tab {
            border:0;background:transparent;color:#9fb0c7;padding:12px 8px;border-radius:11px;
            cursor:pointer;font-size:.9rem;font-weight:750;transition:.25s;
        }
        .tab.active { color:#071b2c;background:linear-gradient(110deg,#83f0df,#8cb7ff);box-shadow:0 7px 20px rgba(87,185,211,.2); }
        .auth-form { display:none;flex-direction:column;gap:15px;position:relative; }
        .auth-form.active { display:flex;animation:appear .35s ease; }
        @keyframes appear { from{opacity:0;transform:translateY(9px)}to{opacity:1;transform:translateY(0)} }
        .field-label { color:#d9e4f2;font-size:.8rem;font-weight:700;margin:0 2px -8px; }
        .input-shell { position:relative; }
        .input-shell>i { position:absolute;right:16px;top:50%;transform:translateY(-50%);color:#8ea6c2;font-size:1rem; }
        .input-shell input {
            width:100%;height:54px;padding:0 48px 0 46px;border-radius:14px;
            border:1px solid rgba(255,255,255,.13);outline:0;color:white;
            background:rgba(4,14,29,.48);font-size:.91rem;transition:.22s;
        }
        .input-shell input::placeholder { color:#8295ae; }
        .input-shell input:focus { border-color:rgba(106,226,216,.75);box-shadow:0 0 0 4px rgba(85,228,210,.1);background:rgba(4,14,29,.7); }
        .reveal {
            position:absolute;left:13px;top:50%;transform:translateY(-50%);border:0;
            background:none;color:#91a5bf;cursor:pointer;padding:7px;font-size:.95rem;
        }
        .submit-btn {
            height:55px;margin-top:5px;border:0;border-radius:14px;cursor:pointer;
            color:#061827;font-size:.96rem;font-weight:900;
            background:linear-gradient(105deg,#83f0df,#8bb5ff);
            box-shadow:0 12px 28px rgba(72,179,196,.2);transition:.25s;
        }
        .submit-btn:hover { transform:translateY(-2px);box-shadow:0 17px 32px rgba(72,179,196,.3);filter:saturate(1.12); }
        .submit-btn i { margin-right:7px; }
        .msg { padding:11px 13px;border-radius:12px;font-size:.82rem;font-weight:700;text-align:center;background:rgba(248,113,113,.1);border:1px solid rgba(248,113,113,.22);color:#ffaaaa; }
        .msg.success { color:#8ff0ce;background:rgba(52,211,153,.1);border-color:rgba(52,211,153,.2); }
        .secure-note { display:flex;align-items:center;justify-content:center;gap:8px;color:#8da2bc;font-size:.73rem;margin-top:21px; }
        .secure-note i { color:#69dfc8; }
        .bottom-note { text-align:center;color:#758aa5;font-size:.72rem;margin-top:17px; }
        @media(max-width:900px) {
            .page { grid-template-columns:1fr;max-width:590px;padding-top:42px;gap:34px; }
            .intro { text-align:center;padding:0; }
            .intro-copy { margin:auto; }
            .feature-row { justify-content:center; }
            .visual-card { margin:28px auto 0;text-align:right; }
            .auth-wrap { justify-self:center;max-width:520px; }
        }
        @media(max-width:600px) {
            .topbar { width:calc(100% - 28px);margin-top:14px;min-height:65px;padding:9px 12px;border-radius:18px; }
            .top-links a:not(.home-link) { display:none; }
            .top-links a { padding:9px 11px;font-size:.78rem; }
            .brand-mark { width:40px;height:40px; }
            .brand-name { font-size:.88rem; }
            .page { width:calc(100% - 30px);padding:34px 0 40px; }
            .intro h1 { font-size:2.45rem;letter-spacing:-1px;margin:20px 0 12px; }
            .intro-copy { font-size:.9rem; }
            .feature { font-size:.74rem;padding:10px 12px; }
            .visual-card { min-height:unset;padding:17px; }
            .auth-card { padding:27px 21px;border-radius:24px; }
            .card-heading h2 { font-size:1.55rem; }
        }
        @media(prefers-reduced-motion:reduce) { *,*:before,*:after { animation:none!important;transition:none!important; } }

        body[data-theme="light"] {
            color:#253550;
            background:radial-gradient(ellipse at 12% 15%,rgba(113,160,239,.22),transparent 35%),
                       radial-gradient(ellipse at 86% 82%,rgba(73,198,173,.17),transparent 35%),
                       linear-gradient(135deg,#f8fbff 0%,#edf4ff 52%,#f5fffc 100%);
        }
        body[data-theme="light"]:before { opacity:.25;background-image:linear-gradient(rgba(50,77,115,.05) 1px,transparent 1px),linear-gradient(90deg,rgba(50,77,115,.05) 1px,transparent 1px); }
        body[data-theme="light"] .topbar { background:rgba(255,255,255,.76);border-color:rgba(110,135,175,.2);box-shadow:0 16px 45px rgba(38,59,95,.09); }
        body[data-theme="light"] .brand,body[data-theme="light"] .brand-name { color:#1d2c47; }
        body[data-theme="light"] .brand-name small { color:#7889a2; }
        body[data-theme="light"] .top-links a { color:#5d6d86; }
        body[data-theme="light"] .top-links a:hover { color:#233d77;background:rgba(75,111,190,.08); }
        body[data-theme="light"] .top-links .home-link { color:#3156a0;border-color:#d5e0f2; }
        body[data-theme="light"] .eyebrow { color:#267d73;background:rgba(57,190,170,.09);border-color:rgba(57,190,170,.23); }
        body[data-theme="light"] .intro h1 { color:#1c3157; }
        body[data-theme="light"] .intro-copy { color:#62738d; }
        body[data-theme="light"] .feature { color:#536681;background:rgba(255,255,255,.65);border-color:rgba(122,146,183,.18); }
        body[data-theme="light"] .visual-card { background:rgba(255,255,255,.72);border-color:rgba(122,146,183,.2);box-shadow:0 12px 35px rgba(40,65,105,.06); }
        body[data-theme="light"] .visual-card strong { color:#263b61; }
        body[data-theme="light"] .visual-card p { color:#71819a; }
        body[data-theme="light"] .auth-card { background:rgba(255,255,255,.76);border-color:rgba(255,255,255,.95);box-shadow:0 30px 80px rgba(35,57,95,.14),inset 0 1px #fff; }
        body[data-theme="light"] .card-logo span { color:#61738f; }
        body[data-theme="light"] .card-heading h2 { color:#1e3153; }
        body[data-theme="light"] .card-heading p { color:#71819a; }
        body[data-theme="light"] .tabs { background:#edf2fa; }
        body[data-theme="light"] .tab { color:#64748d; }
        body[data-theme="light"] .tab.active { color:#102444; }
        body[data-theme="light"] .field-label { color:#405574; }
        body[data-theme="light"] .input-shell input { color:#243550;background:rgba(247,250,255,.96);border-color:#dce5f1; }
        body[data-theme="light"] .input-shell input::placeholder { color:#9aa8bb; }
        body[data-theme="light"] .input-shell>i,body[data-theme="light"] .reveal { color:#7d90aa; }
        body[data-theme="light"] .secure-note { color:#75859b; }
        body[data-theme="light"] .bottom-note { color:#8795a9; }
        .login-topbar {
            width:min(1180px,calc(100% - 64px));min-height:58px;margin:22px auto 0;
            padding:8px 13px 8px 18px;border-radius:999px;
            display:flex;align-items:center;justify-content:space-between;gap:16px;
        }
        .topbar-caption { display:flex;align-items:center;gap:10px;color:#9fb1ca;font-size:.78rem;font-weight:650; }
        .topbar-dot { width:8px;height:8px;border-radius:50%;background:#6ee6d3;box-shadow:0 0 12px rgba(110,230,211,.7); }
        body[data-theme="light"] .topbar-caption { color:#6c7d96; }
        .login-topbar .theme-toggle { margin-right:0; }
        @media(max-width:600px) {
            .login-topbar { width:calc(100% - 28px);margin-top:14px;padding:7px 9px 7px 12px; }
            .topbar-caption { font-size:.68rem; }
        }


        .theme-toggle {
            display:inline-flex;align-items:center;justify-content:center;gap:10px;
            min-height:44px;padding:7px 13px 7px 9px;border-radius:999px;cursor:pointer;
            color:#e9f4ff;background:linear-gradient(120deg,rgba(255,255,255,.105),rgba(255,255,255,.045));
            border:1px solid rgba(255,255,255,.2);font:750 .78rem 'Vazirmatn',sans-serif;
            white-space:nowrap;transition:background .3s,border-color .3s,box-shadow .3s,transform .3s;
            box-shadow:inset 0 1px rgba(255,255,255,.08),0 5px 18px rgba(0,0,0,.1);
        }
        .theme-toggle:hover { transform:translateY(-1px);border-color:rgba(104,229,210,.55);box-shadow:0 8px 24px rgba(55,190,181,.13); }
        .theme-toggle .theme-icon {
            width:29px;height:29px;display:grid;place-items:center;border-radius:50%;
            color:#082033;background:linear-gradient(145deg,#8af3e4,#8bb5ff);
            box-shadow:0 3px 10px rgba(85,228,210,.2);font-size:.86rem;
        }
        .theme-toggle .theme-label { letter-spacing:-.15px; }
        .theme-toggle .theme-track {
            width:34px;height:19px;padding:3px;border-radius:30px;
            background:rgba(255,255,255,.15);border:1px solid rgba(255,255,255,.13);
            display:flex;align-items:center;justify-content:flex-start;transition:.3s;
        }
        .theme-toggle .theme-track span { width:11px;height:11px;border-radius:50%;background:#8cebdc;box-shadow:0 0 8px rgba(104,229,210,.5);transition:.3s; }
        body[data-theme="light"] .theme-toggle { color:#315078;background:linear-gradient(120deg,rgba(255,255,255,.96),rgba(239,246,255,.9));border-color:#dce6f3;box-shadow:inset 0 1px #fff,0 6px 18px rgba(49,75,115,.08); }
        body[data-theme="light"] .theme-toggle .theme-icon { color:white;background:linear-gradient(145deg,#5d7ee5,#8aa8f6);box-shadow:0 3px 10px rgba(85,120,220,.2); }
        body[data-theme="light"] .theme-toggle .theme-track { justify-content:flex-end;background:#e8edf8;border-color:#dbe4f2; }
        body[data-theme="light"] .theme-toggle .theme-track span { background:#718de9;box-shadow:0 0 8px rgba(113,141,233,.35); }


        /* Final polish: cohesive award-inspired login experience */
        body { isolation:isolate; }
        body:after { content:"";position:fixed;inset:0;pointer-events:none;z-index:0;opacity:.12;background-image:url("data:image/svg+xml,%3Csvg viewBox='0 0 180 180' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='.2'/%3E%3C/svg%3E");mix-blend-mode:soft-light; }
        .topbar,.page { position:relative;z-index:1; }
        .topbar { transition:border-color .25s,background .25s,transform .25s; }
        .topbar:hover { border-color:rgba(126,210,224,.25); }
        .brand-mark { position:relative;overflow:hidden; }
        .brand-mark:after { content:"";position:absolute;inset:-80% auto -80% -50%;width:38%;transform:rotate(25deg);background:rgba(255,255,255,.38);transition:left .55s; }
        .brand:hover .brand-mark:after { left:130%; }
        .intro { animation:ario-intro .8s cubic-bezier(.2,.7,.2,1) both; }
        .auth-wrap { animation:ario-card .85s .08s cubic-bezier(.2,.7,.2,1) both; }
        @keyframes ario-intro { from{opacity:0;transform:translateY(20px)}to{opacity:1;transform:translateY(0)} }
        @keyframes ario-card { from{opacity:0;transform:translateY(24px) scale(.985)}to{opacity:1;transform:translateY(0) scale(1)} }
        .auth-card { transition:transform .3s,border-color .3s,box-shadow .3s; }
        .auth-card:hover { border-color:rgba(133,213,226,.28);box-shadow:0 40px 110px rgba(0,0,0,.4),inset 0 1px rgba(255,255,255,.14); }
        .feature { transition:transform .22s,border-color .22s,background .22s; }
        .feature:hover { transform:translateY(-3px);border-color:rgba(113,226,215,.28);background:rgba(255,255,255,.075); }
        .input-shell input { transition:border-color .22s,box-shadow .22s,background .22s,transform .22s; }
        .input-shell input:focus { transform:translateY(-1px); }
        .submit-btn { position:relative;overflow:hidden; }
        .submit-btn:before { content:"";position:absolute;top:-80%;bottom:-80%;left:-35%;width:22%;transform:rotate(22deg);background:rgba(255,255,255,.34);transition:left .55s; }
        .submit-btn:hover:before { left:125%; }
        @media(max-width:600px) { .page { gap:28px; } .visual-card { margin-top:22px; } .auth-wrap { width:100%; } }
        @media(prefers-reduced-motion:reduce) { .intro,.auth-wrap { animation:none!important; } }

    
/* Refined login palette: navy, porcelain blue and champagne */
:root{--cyan:#d8bd8a!important}
body{
 background:
 radial-gradient(ellipse at 12% 15%,rgba(95,130,190,.20),transparent 34%),
 radial-gradient(ellipse at 86% 82%,rgba(216,189,138,.09),transparent 34%),
 linear-gradient(135deg,#06101f 0%,#0a1d35 52%,#071426 100%)!important;
}
.ambient.b{background:radial-gradient(circle,rgba(216,189,138,.12),transparent 68%)!important}
.brand-mark{
 background:linear-gradient(145deg,#e4cfaa,#9bb8ed)!important;
 color:#102039!important;
 box-shadow:0 8px 25px rgba(216,189,138,.16)!important;
 border-radius:17px 8px 17px 8px!important;
}
.intro:before{border-radius:30px 10px 30px 10px!important}
.eyebrow{color:#e4cda3!important;background:rgba(216,189,138,.08)!important;border-color:rgba(216,189,138,.22)!important}
.intro h1 span{background:linear-gradient(100deg,#d8bd8a 8%,#9bb8ed 75%)!important;-webkit-background-clip:text!important;background-clip:text!important}
.feature,.visual-card,.auth-card{border-radius:26px 10px 26px 10px!important}
.feature i,.visual-icon{color:#dfc69a!important}
.submit-btn{background:linear-gradient(115deg,#d8bd8a,#ead9b7)!important;color:#13233a!important;border-radius:999px!important}
.topbar{border-radius:26px!important}
.top-links a{border-radius:999px!important}
input:focus{border-color:#9bb8ed!important;box-shadow:0 0 0 4px rgba(155,184,237,.13)!important}


/* LOGIN PAGE VISIBILITY + NAVY / ICE BLUE PALETTE */
.page{align-items:center!important;min-height:calc(100vh - 125px)!important}
.intro{display:block!important;visibility:visible!important;opacity:1!important;color:#f5f7fc!important;z-index:2!important}
.intro>*{visibility:visible!important;opacity:1!important}
.intro h1{color:#f5f7fc!important}
.intro h1 span{background:linear-gradient(100deg,#dce7ff 5%,#9eb8ed 58%,#c5d4f5 100%)!important;-webkit-background-clip:text!important;background-clip:text!important;color:transparent!important}
.intro-copy{color:#c1cde0!important}
.eyebrow{color:#c9d8fa!important;background:rgba(153,181,235,.10)!important;border-color:rgba(171,196,240,.24)!important}
.eyebrow i,.feature i,.visual-icon{color:#c1d2f5!important}
.feature{color:#d3dced!important;border-color:rgba(205,220,245,.15)!important;background:rgba(255,255,255,.055)!important}
.visual-card{background:linear-gradient(130deg,rgba(255,255,255,.11),rgba(255,255,255,.035))!important;border-color:rgba(205,220,245,.17)!important}
.visual-card strong{color:#f2f6ff!important}.visual-card p{color:#bdc9dc!important}
.auth-card{border-radius:30px 30px 30px 8px!important;border-color:rgba(196,214,245,.2)!important}
.tab.active,.submit-btn{background:linear-gradient(110deg,#dce7fb,#a9c0ef)!important;color:#142743!important}
.input-shell input:focus{border-color:rgba(166,194,242,.8)!important;box-shadow:0 0 0 4px rgba(143,174,230,.13)!important}
.secure-note i{color:#a9c0ed!important}
.login-topbar{background:rgba(12,27,48,.48)!important;border:1px solid rgba(205,220,245,.2)!important;-webkit-backdrop-filter:blur(24px) saturate(145%)!important;backdrop-filter:blur(24px) saturate(145%)!important;box-shadow:0 14px 42px rgba(0,0,0,.18)!important}
body[data-theme="light"] .intro h1{color:#1b2d4a!important}
body[data-theme="light"] .intro-copy{color:#596d8b!important}
body[data-theme="light"] .eyebrow{color:#49699e!important;background:rgba(115,151,215,.1)!important;border-color:rgba(115,151,215,.22)!important}
body[data-theme="light"] .feature{color:#536987!important;background:rgba(255,255,255,.72)!important;border-color:#dce5f2!important}
body[data-theme="light"] .visual-card{background:rgba(255,255,255,.78)!important;border-color:#dce5f2!important}
body[data-theme="light"] .visual-card strong{color:#263c60!important}
body[data-theme="light"] .visual-card p{color:#657895!important}
body[data-theme="light"] .login-topbar{background:rgba(250,252,255,.72)!important;border-color:rgba(118,143,181,.24)!important}
body[data-theme="light"] .topbar-caption{color:#405779!important}
@media(max-width:900px){.page{grid-template-columns:1fr!important;gap:32px!important}.intro{padding:22px 12px!important;text-align:center!important}.intro:before{inset:-10px!important;border-radius:25px!important}.feature-row{justify-content:center!important}.visual-card{margin-inline:auto!important;text-align:right!important}.auth-wrap{justify-self:center!important}}

        
/* Login theme synchronization: switch every visible layer together */
body[data-theme="light"]{
 background:radial-gradient(ellipse at 12% 12%,rgba(133,164,218,.22),transparent 35%),radial-gradient(ellipse at 88% 86%,rgba(176,195,226,.22),transparent 34%),linear-gradient(135deg,#f8faff 0%,#eaf0f9 54%,#f7faff 100%)!important;
 color:#203451!important
}
body[data-theme="light"]:before{opacity:.42!important;background-image:linear-gradient(rgba(60,86,128,.045) 1px,transparent 1px),linear-gradient(90deg,rgba(60,86,128,.045) 1px,transparent 1px)!important}
body[data-theme="light"] .ambient.a{background:radial-gradient(circle,rgba(108,145,205,.18),transparent 68%)!important}
body[data-theme="light"] .ambient.b{background:radial-gradient(circle,rgba(150,174,216,.2),transparent 68%)!important}
body[data-theme="light"] .intro:before{
 background:linear-gradient(90deg,rgba(246,249,255,.96),rgba(246,249,255,.88) 60%,rgba(246,249,255,.55)),url('https://images.unsplash.com/photo-1498243691581-b145c3f54a5a?auto=format&fit=crop&w=1400&q=90') center/cover!important;
 opacity:1!important;box-shadow:0 25px 70px rgba(40,62,101,.1)!important;border:1px solid rgba(133,157,196,.18)!important
}
body[data-theme="light"] .intro h1{color:#1c3152!important}
body[data-theme="light"] .intro h1 span{background:linear-gradient(100deg,#47699f,#7896c8,#536f9f)!important;-webkit-background-clip:text!important;background-clip:text!important;color:transparent!important}
body[data-theme="light"] .intro-copy{color:#526783!important}
body[data-theme="light"] .feature{color:#405675!important;background:rgba(255,255,255,.68)!important;border-color:rgba(116,142,184,.22)!important}
body[data-theme="light"] .feature i{color:#5879ad!important}
body[data-theme="light"] .visual-card{background:rgba(255,255,255,.72)!important;border-color:rgba(123,148,189,.24)!important;box-shadow:0 12px 35px rgba(39,61,99,.07)!important}
body[data-theme="light"] .visual-card strong{color:#263d60!important}
body[data-theme="light"] .visual-card p{color:#60748f!important}
body[data-theme="light"] .visual-icon{color:#49699e!important;background:linear-gradient(145deg,#e6edfa,#f6f8fd)!important}
body[data-theme="light"] .topbar{background:rgba(255,255,255,.72)!important;border-color:rgba(125,149,187,.23)!important;box-shadow:0 16px 45px rgba(38,59,95,.08)!important}
body[data-theme="light"] .topbar-caption{color:#425a7d!important}
body[data-theme="light"] .brand,body[data-theme="light"] .brand-name{color:#203451!important}
body[data-theme="light"] .brand-name small{color:#70819b!important}
body[data-theme="light"] .auth-card{background:rgba(255,255,255,.83)!important;border-color:rgba(255,255,255,.95)!important;box-shadow:0 28px 75px rgba(43,64,101,.13)!important}
body[data-theme="light"] .card-heading h2{color:#203451!important}
body[data-theme="light"] .card-heading p{color:#6a7b94!important}
body[data-theme="light"] .field-label{color:#425a7d!important}
body[data-theme="light"] .input-shell input{background:#f8faff!important;color:#203451!important;border-color:#dce5f1!important}
body[data-theme="light"] .input-shell input::placeholder{color:#9aa9bd!important}
body[data-theme="light"] .secure-note,body[data-theme="light"] .bottom-note{color:#71819a!important}
body[data-theme="light"] .tabs{background:#edf2fa!important}
body[data-theme="light"] .tab{color:#687b96!important}
body[data-theme="light"] .tab.active{color:#203451!important;background:#fff!important;box-shadow:0 3px 12px rgba(44,65,103,.08)!important}
body[data-theme="light"] .submit-btn{background:linear-gradient(110deg,#506fa8,#7897c9)!important;color:#fff!important}
body[data-theme="light"] .login-topbar{background:rgba(255,255,255,.72)!important;border-color:rgba(125,149,187,.23)!important}

        
html[lang="en"] body, html[lang="en"] body * {
  font-family: Inter, "Segoe UI", Arial, sans-serif !important;
}
html[lang="en"] body { direction:ltr !important; text-align:left; }
html[lang="en"] header, html[lang="en"] nav, html[lang="en"] .auth-btns,
html[lang="en"] .login-topbar-actions { direction:ltr !important; }
html[lang="en"] .container, html[lang="en"] .inner-page,
html[lang="en"] .story-layout, html[lang="en"] .editorial-inner { direction:ltr !important; }
html[lang="en"] .page-title, html[lang="en"] .hero-card { text-align:left; }
html[lang="en"] .input-shell input { text-align:left !important; direction:ltr !important; }
html[lang="en"] .input-shell>i { right:auto !important; left:16px !important; }
html[lang="en"] .input-shell input { padding:0 46px 0 48px !important; }
html[lang="en"] .reveal { left:auto !important; right:13px !important; }
html[lang="en"] .intro, html[lang="en"] .auth-card,
html[lang="en"] .inner-hero-copy, html[lang="en"] .story-main,
html[lang="en"] .story-side { text-align:left !important; }
html[lang="en"] .intro { padding:34px 0 34px 30px !important; }
html[lang="en"] .intro:before { inset:-30px -80px -30px -45px !important; }
html[lang="en"] .feature-row { justify-content:flex-start !important; }
html[lang="en"] .secure-note, html[lang="en"] .bottom-note { text-align:center !important; }
html[lang="en"] .hero-content { text-align:left !important; }
html[lang="en"] .hero-cta { justify-content:flex-start !important; }
html[lang="en"] .hero-caption { direction:ltr !important; }
html[lang="en"] .staff-list, html[lang="en"] .experience-list,
html[lang="en"] .journal-list, html[lang="en"] .contact-editorial-grid { direction:ltr !important; }
html[lang="en"] .admin-list-item, html[lang="en"] .admin-form { direction:ltr !important; }
html[lang="en"] .admin-section h3 { text-align:left !important; }
html[lang="en"] .login-topbar-actions { margin-left:auto; }
.language-toggle { min-width:78px; }

</style>
    <script>
        function switchTab(tabId) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.auth-form').forEach(f => f.classList.remove('active'));
            document.getElementById('tab-' + tabId).classList.add('active');
            document.getElementById('form-' + tabId).classList.add('active');
        }
        function togglePassword(id, button) {
            const field = document.getElementById(id);
            const hidden = field.type === 'password';
            field.type = hidden ? 'text' : 'password';
            button.innerHTML = hidden ? '<i class="fa-solid fa-eye-slash"></i>' : '<i class="fa-solid fa-eye"></i>';
            button.setAttribute('aria-label', hidden ? 'مخفی کردن رمز' : 'نمایش رمز');
        }
        document.addEventListener('DOMContentLoaded', function () {
            const showRegister = {{ 'true' if show_register else 'false' }};
            if (showRegister) switchTab('register');
        });
    </script>
</head>
<body>
    <div class="ambient a"></div><div class="ambient b"></div>
    <header class="topbar login-topbar">
        <div class="topbar-caption"><span class="topbar-dot"></span> فضای اختصاصی مدرسه آریو مصلی‌نژاد</div>
        <div class="login-topbar-actions">
        <button class="language-toggle" type="button" data-language-toggle onclick="toggleArioLanguage()">English</button>
        <button class="theme-toggle" type="button" data-theme-toggle onclick="toggleArioTheme()">
            <span class="theme-icon"><i class="fa-solid fa-sun"></i></span>
            <span class="theme-label">پوسته روشن</span>
            <span class="theme-track"><span></span></span>
        </button>
        </div>
    </header>

    <main class="page">
        <section class="intro">
            <div class="eyebrow"><i class="fa-solid fa-sparkles"></i> به فضای یادگیری آریو خوش آمدید</div>
            <h1>آینده از همین‌جا<br><span>شروع می‌شود.</span></h1>
            <p class="intro-copy">
                اینجا نقطه اتصال ایده‌ها، تلاش‌ها و اتفاق‌های خوب مدرسه آریو مصلی‌نژاد است.
                وارد حساب خود شوید و همراه جامعه مدرسه، قدم بعدی را بسازید.
            </p>
            <div class="feature-row">
                <div class="feature"><i class="fa-solid fa-shield-halved"></i> فضای امن و اختصاصی</div>
                <div class="feature"><i class="fa-solid fa-bolt"></i> دسترسی سریع و ساده</div>
                <div class="feature"><i class="fa-solid fa-graduation-cap"></i> همراه مسیر رشد</div>
            </div>
            <div class="visual-card">
                <div class="visual-icon"><i class="fa-solid fa-lightbulb"></i></div>
                <div>
                    <strong>هر روز، یک فرصت تازه برای درخشیدن</strong>
                    <p>با هم یاد می‌گیریم، تجربه می‌کنیم و آینده‌ای بهتر می‌سازیم.</p>
                </div>
            </div>
        </section>

        <section class="auth-wrap">
            <div class="auth-card">
                <div class="card-heading">
                    <div class="card-logo"><div class="brand-mark">آ</div><span>سامانه یکپارچه مدرسه</span></div>
                    <h2>اینجا شروعِ اتفاق‌های بزرگه ✨</h2>
                    <p>برای ادامه مسیر، وارد حساب کاربری‌ات شو یا حساب جدید بساز.</p>
                </div>
                <div class="tabs">
                    <button type="button" id="tab-login" class="tab active" onclick="switchTab('login')">ورود به حساب</button>
                    <button type="button" id="tab-register" class="tab" onclick="switchTab('register')">ایجاد حساب</button>
                </div>
                <form id="form-login" class="auth-form active" action="/login" method="POST">
                    <label class="field-label" for="login-username">نام کاربری</label>
                    <div class="input-shell"><i class="fa-regular fa-user"></i><input id="login-username" type="text" name="username" placeholder="نام کاربری خود را وارد کنید" autocomplete="username" required></div>
                    <label class="field-label" for="login-password">رمز عبور</label>
                    <div class="input-shell"><i class="fa-solid fa-lock"></i><input id="login-password" type="password" name="password" placeholder="رمز عبور" autocomplete="current-password" required><button class="reveal" type="button" onclick="togglePassword('login-password',this)" aria-label="نمایش رمز"><i class="fa-solid fa-eye"></i></button></div>
                    <button class="submit-btn" type="submit">ورود به سامانه <i class="fa-solid fa-arrow-left"></i></button>
                    {% if error and not show_register %}<div class="msg">{{ error }}</div>{% endif %}
                    {% if success %}<div class="msg success">{{ success }}</div>{% endif %}
                </form>
                <form id="form-register" class="auth-form" action="/register" method="POST">
                    <label class="field-label" for="register-username">نام کاربری دلخواه</label>
                    <div class="input-shell"><i class="fa-regular fa-user"></i><input id="register-username" type="text" name="username" placeholder="یک نام کاربری انتخاب کنید" autocomplete="username" required></div>
                    <label class="field-label" for="register-password">رمز عبور</label>
                    <div class="input-shell"><i class="fa-solid fa-lock"></i><input id="register-password" type="password" name="password" placeholder="یک رمز عبور بسازید" autocomplete="new-password" required><button class="reveal" type="button" onclick="togglePassword('register-password',this)" aria-label="نمایش رمز"><i class="fa-solid fa-eye"></i></button></div>
                    <button class="submit-btn" type="submit">ساخت حساب کاربری <i class="fa-solid fa-arrow-left"></i></button>
                    {% if error and show_register %}<div class="msg">{{ error }}</div>{% endif %}
                </form>
                <div class="secure-note"><i class="fa-solid fa-shield-halved"></i> اطلاعات حساب شما در محیطی امن نگهداری می‌شود</div>
                <div class="bottom-note">© مدرسه آریو مصلی‌نژاد · با افتخار برای جامعه مدرسه</div>
            </div>
        </section>
    </main>

<script>
(function () {
    const key = 'ario-signature-theme-v2';
    function applyTheme(theme) {
        document.body.setAttribute('data-theme', theme);
        document.querySelectorAll('[data-theme-toggle]').forEach(function (button) {
            const light = theme === 'light';
            button.innerHTML = light
                ? '<i class="fa-solid fa-moon"></i><span>حالت تیره</span>'
                : '<i class="fa-solid fa-sun"></i><span>حالت روشن</span>';
            button.setAttribute('aria-label', light ? 'فعال‌کردن حالت تیره' : 'فعال‌کردن حالت روشن');
            button.setAttribute('title', light ? 'فعال‌کردن حالت تیره' : 'فعال‌کردن حالت روشن');
        });
    }
    window.toggleArioTheme = function () {
        const next = document.body.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
        try { localStorage.setItem(key, next); } catch (e) {}
        applyTheme(next);
    };
    let saved = 'dark';
    try { saved = localStorage.getItem(key) || 'dark'; } catch (e) {}
    applyTheme(saved);
    document.addEventListener('DOMContentLoaded', function () { applyTheme(saved); });
})();
</script>


<script>
(function () {
  const dictionary = {
    "مدرسه آریو مصلی‌نژاد": "Ario Mosallinejad School",
    "آریو مصلی‌نژاد": "Ario Mosallinejad",
    "دولتی - ارومیه": "Public School · Urmia",
    "مدرسه آریو مصلی‌نژاد | {{ title }}": "Ario Mosallinejad School | {{ title }}",
    "ورود به آریو | مدرسه آریو مصلی‌نژاد": "Sign in to Ario | Ario Mosallinejad School",
    "آ": "A",
    "خانه": "Home",
    "درباره ما": "About Us",
    "کادر مدرسه": "Our Team",
    "فعالیت‌ها": "Activities",
    "اخبار": "News",
    "تماس": "Contact",
    "تماس با ما": "Contact Us",
    "پنل مدیریت": "Admin Panel",
    "پنل مدیریت پیشرفته": "Advanced Admin Panel",
    "حالت روشن": "Light Mode",
    "حالت تیره": "Dark Mode",
    "پوسته روشن": "Light Theme",
    "پوسته تیره": "Dark Theme",
    "خروج": "Log Out",
    "ورود": "Sign In",
    "مدیر سایت (شما)": "Website Administrator",
    "مدیر مدرسه": "School Principal",
    "معلم": "Teacher",
    "دانش‌آموز": "Student",
    "اصلی": "Primary",
    "ویرایش": "Edit",
    "حذف": "Delete",
    "افزودن": "Add",
    "انصراف": "Cancel",
    "ثبت ویرایش": "Save Changes",
    "ذخیره متون": "Save Text",
    "ذخیره و انتشار خبر": "Save & Publish News",
    "افزودن کاربر": "Add User",
    "آمار مدرسه": "School Statistics",
    "فضای اختصاصی مدرسه آریو مصلی‌نژاد": "Ario School Private Portal",
    "به فضای یادگیری آریو خوش آمدید": "Welcome to Ario's Learning Community",
    "آینده از همین‌جا": "The Future",
    "شروع می‌شود.": "Starts Here.",
    "اینجا نقطه اتصال ایده‌ها، تلاش‌ها و اتفاق‌های خوب مدرسه آریو مصلی‌نژاد است.": "A place where ideas, effort, and memorable moments come together at Ario School.",
    "وارد حساب خود شوید و همراه جامعه مدرسه، قدم بعدی را بسازید.": "Sign in and take your next step with the Ario community.",
    "فضای امن و اختصاصی": "A Safe, Dedicated Space",
    "دسترسی سریع و ساده": "Quick and Easy Access",
    "همراه مسیر رشد": "Here for Every Step of Growth",
    "هر روز، یک فرصت تازه برای درخشیدن": "Every Day Is a New Chance to Shine",
    "با هم یاد می‌گیریم، تجربه می‌کنیم و آینده‌ای بهتر می‌سازیم.": "We learn, explore, and build a better future together.",
    "سامانه یکپارچه مدرسه": "Integrated School Platform",
    "اینجا شروعِ اتفاق‌های بزرگه ✨": "Great Things Start Here ✨",
    "برای ادامه مسیر، وارد حساب کاربری‌ات شو یا حساب جدید بساز.": "Sign in to continue, or create a new account.",
    "ورود به حساب": "Sign In",
    "ایجاد حساب": "Create Account",
    "نام کاربری": "Username",
    "نام کاربری دلخواه": "Choose a Username",
    "رمز عبور": "Password",
    "ورود به سامانه": "Sign In",
    "نام کاربری جدید": "New Username",
    "ساخت حساب کاربری": "Create Account",
    "اطلاعات حساب شما در محیطی امن نگهداری می‌شود": "Your account information is stored securely.",
    "© مدرسه آریو مصلی‌نژاد · با افتخار برای جامعه مدرسه": "© Ario Mosallinejad School · Made with pride for our school community",
    "· جایی برای یادگیری، تجربه و ساختن آینده": "· A place to learn, explore, and shape the future",
    "آینده را با هم می‌سازیم.": "We Build the Future Together.",
    "اینجا ایده‌ها جان می‌گیرند و قدم‌های کوچک، آینده را می‌سازند.": "Ideas come to life here, and small steps shape the future.",
    "اینجا، آریو": "This Is Where",
    "زندگی می‌کند.": "Ario Comes to Life.",
    "آریو، فراتر از کلاس درس": "Ario Is More Than a Classroom",
    "در آریو، هر پرسش دریچه‌ای تازه است؛ با تجربه کردن، همکاری و کشف استعدادها، برای ساختن فردایی روشن‌تر آماده می‌شویم.": "At Ario, every question opens a new door. Through hands-on learning, teamwork, and discovering our talents, we prepare to shape a brighter tomorrow.",
    "عضو معرفی‌شده کادر": "Team Members",
    "فعالیت دانش‌آموزی": "Student Activities",
    "خبر و رویداد": "News & Events",
    "یادگیری · دوستی · کشف": "LEARNING · FRIENDSHIP · DISCOVERY",
    "تجربه‌های آریو": "Explore Ario",
    "داستان ما": "Our Story",
    "اینجا فرصت داریم کنجکاوی کنیم، مهارت‌های تازه بیاموزیم، دوستی بسازیم و توانایی‌هایمان را به دستاورد تبدیل کنیم.": "Here, we ask questions, learn new skills, build friendships, and turn our potential into meaningful achievements.",
    "کنجکاوی،": "Curiosity",
    "شروعِ هر اتفاق بزرگ است.": "Is Where Great Things Begin.",
    "یادگیری واقعی با یک پرسش آغاز می‌شود؛ با ایده‌پردازی، تجربه و همکاری ادامه پیدا می‌کند و به ساختن راه‌های تازه می‌رسد.": "Real learning begins with a question. It grows through ideas, experience, and teamwork—and leads to new possibilities.",
    "بیشتر درباره فعالیت‌ها": "Discover Our Activities",
    "هر روز، یک قدم به سوی آینده‌ای بهتر.": "Every Day, One Step Toward a Brighter Future.",
    "با مدرسه در ارتباط باش": "Connect With Our School",
    "یک مدرسه؛": "One School;",
    "هزاران امکان.": "A Thousand Possibilities.",
    "داستان ما درباره رشد، رفاقت و ساختن فردایی روشن‌تر است.": "Our story is about growth, friendship, and creating a brighter tomorrow.",
    "آریو را": "Discover",
    "بشناس.": "Ario.",
    "مدرسه، فقط یک ساختمان و چند کلاس نیست؛ جایی است که شخصیت، رویا و آینده شکل می‌گیرد.": "A school is more than a building and classrooms; it is where character, dreams, and futures take shape.",
    "ما باور داریم هر دانش‌آموز استعداد و مسیر منحصربه‌فرد خودش را دارد. وظیفه ما فراهم کردن فضایی امن، پویا و الهام‌بخش برای کشف این توانایی‌هاست.": "We believe every student has unique talents and a path of their own. Our mission is to create a safe, vibrant, and inspiring environment where those abilities can flourish.",
    "برای پرسیدن، کشف کردن و پیدا کردن پاسخ‌های تازه.": "To ask questions, explore, and find new answers.",
    "رشد در کنار یکدیگر و یاد گرفتن از تفاوت‌ها.": "Growing together and learning from our differences.",
    "قدم‌های کوچک و پیوسته برای ساختن آینده‌ای بهتر.": "Small, consistent steps toward a better future.",
    "کنجکاوی": "Curiosity",
    "همراهی": "Togetherness",
    "پیشرفت": "Progress",
    "آدم‌های": "The People",
    "اثرگذار": "Who Make a Difference",
    "آریو.": "At Ario.",
    "یک تیم؛": "One Team;",
    "یک مسیر.": "One Journey.",
    "آدم‌هایی که هر روز با دانش، تعهد و همراهی، مسیر رشد را روشن‌تر می‌کنند.": "People who bring knowledge, commitment, and care to make every student's path brighter.",
    "OUR COMMUNITY": "OUR COMMUNITY",
    "پشت هر تجربه خوب در مدرسه، آدم‌هایی هستند که با عشق و مسئولیت کار می‌کنند.": "Behind every meaningful school experience are people who work with care and responsibility.",
    "کادر آریو همراه دانش‌آموزان است تا فضایی امن، پویا و الهام‌بخش برای یادگیری و شکوفایی استعدادها شکل بگیرد.": "The Ario team works alongside students to create a safe, dynamic, and inspiring environment for learning and growth.",
    "اطلاعات کادر مدرسه هنوز ثبت نشده است.": "Team information has not been added yet.",
    "کلاس درس،": "The Classroom",
    "تمام ماجرا نیست.": "Is Only the Beginning.",
    "ایده‌ها وقتی زنده می‌شوند که آن‌ها را تجربه کنیم.": "Ideas Come Alive When We Put Them Into Practice.",
    "یادگیری": "Learning",
    "در جریان است.": "In Motion.",
    "هر تجربه، فرصتی برای کشف توانایی‌های تازه است.": "Every experience is an opportunity to discover new abilities.",
    "از همکاری و هنر تا فناوری و فعالیت‌های گروهی؛ آریو یادگیری را به تجربه‌ای زنده و ماندگار تبدیل می‌کند.": "From teamwork and the arts to technology and group projects, Ario turns learning into a meaningful, lasting experience.",
    "تجربه آریو": "The Ario Experience",
    "هنوز فعالیتی ثبت نشده است.": "No activities have been added yet.",
    "روایت روزهای": "Stories From",
    "پر اتفاق آریو.": "Life at Ario.",
    "خبرها، لحظه‌ها و اتفاق‌هایی که ارزش به خاطر سپردن دارند.": "News, moments, and events worth remembering.",
    "خبرهای": "School",
    "مدرسه.": "News.",
    "هر روز در آریو داستانی تازه برای گفتن وجود دارد.": "Every day at Ario brings a new story to tell.",
    "اینجا می‌توانید خبرها، رویدادها و لحظه‌های مهم جامعه مدرسه را دنبال کنید.": "Follow the latest news, events, and important moments from our school community.",
    "خبر مدرسه": "School News",
    "هنوز خبری منتشر نشده است. به‌زودی اینجا پر از خبرهای تازه می‌شود.": "No news has been published yet. Check back soon for updates.",
    "راه‌های": "Ways to",
    "ارتباط": "Connect",
    "با ما.": "With Us.",
    "برای پرسش، پیشنهاد یا آشنایی بیشتر، خوشحال می‌شویم صدایتان را بشنویم.": "For questions, suggestions, or to learn more, we would be happy to hear from you.",
    "با ما": "Get in",
    "در تماس باش.": "Touch.",
    "ارتباط خوب، شروع یک همکاری ارزشمند است.": "Good communication is the beginning of a valuable partnership.",
    "برای دریافت راهنمایی یا مطرح‌کردن پرسش‌هایتان، از راه‌های زیر با مدرسه آریو در ارتباط باشید.": "For assistance or questions, contact Ario School using the details below.",
    "آدرس مدرسه": "School Address",
    "ارومیه، محله بزرگباش، اول خیابان جانبازان": "Janbazan Street, Bozorgbash, Urmia, Iran",
    "تلفن تماس": "Phone",
    "باز کردن در نقشه": "Open in Maps",
    "مدیریت تمام بخش‌های سایت بدون نیاز به کدنویسی": "Manage every part of the website without coding.",
    "کاربران سامانه": "Platform Users",
    "حساب‌های ثبت‌شده": "Registered Accounts",
    "اعضای کادر": "Team Members",
    "معرفی‌شده در سایت": "Featured on the Website",
    "فعالیت‌ها": "Activities",
    "تجربه‌های مدرسه": "School Experiences",
    "خبرها": "News",
    "مطالب منتشرشده": "Published Posts",
    "مدیریت کاربران (ادمین‌ها و معلم‌ها)": "User Management (Administrators & Teachers)",
    "عنوان بزرگ صفحه خانه": "Homepage Main Heading",
    "متن زیر عنوان صفحه خانه": "Homepage Subtitle",
    "متن صفحه درباره ما": "About Us Page Text",
    "ویرایش متن‌های اصلی": "Edit Main Website Text",
    "انتشار خبر جدید": "Publish a News Article",
    "خبر پس از ذخیره در صفحه «اخبار» نمایش داده می‌شود و با خروج از حساب حذف نخواهد شد.": "After saving, this article will appear on the News page and will remain published after you log out.",
    "افزودن کارت جدید به هر بخش": "Add a New Card to Any Section",
    "صفحه خانه": "Home Page",
    "عنوان": "Title",
    "توضیحات": "Description",
    "مدیر": "Principal",
    "معاون": "Deputy",
    "ستاره": "Star",
    "کامپیوتر": "Computer",
    "کتاب": "Book",
    "مدرسه": "School",
    "جام": "Trophy",
    "در حال ویرایش کارت: {{ edit_card.title }}": "Editing card: {{ edit_card.title }}",
    "لیست تمام کارت‌ها": "All Cards",
    "صفحه خانه (Home)": "Home Page",
    "کادر مدرسه (Staff)": "School Team",
    "فعالیت‌ها (Activities)": "Activities",
    "اخبار (News)": "News",
    "نام کاربری خود را وارد کنید": "Enter your username",
    "یک نام کاربری انتخاب کنید": "Choose a username",
    "یک رمز عبور بسازید": "Create a password",
    "عنوان خبر": "News Title",
    "متن خبر": "News Content",
    "تاریخ خبر (اختیاری؛ مثلاً ۱۴۰۵/۰۸/۲۹)": "News Date (Optional, e.g. 2026/11/20)",
    "لینک تصویر خبر (اختیاری)": "News Image URL (Optional)",
    "متن کامل خبر را بنویسید...": "Write the full news article...",
    "توضیحات": "Description",
    "این کارت حذف شود؟": "Delete this card?",
    "مطمئنی می‌خوای این کاربر رو حذف کنی؟": "Are you sure you want to delete this user?",
    "مخفی کردن رمز": "Hide password",
    "نمایش رمز": "Show password",
    "نام کاربری باید ۳ تا ۳۲ نویسه و رمز عبور حداقل ۶ نویسه باشد.": "Username must be 3–32 characters and password must be at least 6 characters.",
    "نام کاربری و رمز عبور را کامل وارد کنید.": "Please enter both your username and password.",
    "نام کاربری یا رمز عبور اشتباه است.": "Incorrect username or password.",
    "این نام کاربری قبلا وجود دارد!": "This username is already taken.",
    "ثبت‌نام موفق! حالا با همین اطلاعات وارد شوید.": "Registration successful! You can now sign in with your new account.",
    "شما دسترسی به این بخش ندارید.": "You do not have permission to access this section.",
    "بازگشت": "Go Back",
    "جناب آقای سلاطین": "Mr. Salatin",
    "جناب آقای الوانی": "Mr. Alvani",
    "مدیر مدرسه": "School Principal",
    "معاون آموزشی": "Academic Deputy",
    "گروه هنری و تئاتر": "Arts & Theatre Group",
    "اجرای نمایش‌های زیبا در مناسبت‌های مختلف.": "Performing plays and shows for special occasions.",
    "نشریه دانش‌آموزی": "Student Magazine",
    "قلم و ایده دانش‌آموزان در قالب نشریه.": "Student writing and ideas shared through a school magazine.",
    "المپیاد ورزشی": "School Sports Tournament",
    "رقابت سالم و پرشاط بین کلاس‌ها.": "Friendly and energetic competitions between classes.",
    "روز دانش‌آموز": "Student Day",
    "روز دانش‌آموز، روز تجلیل از آینده‌سازان این مرز و بوم است.": "Student Day celebrates the young people who will shape our future.",
    "ما کی هستیم": "Who We Are",
    "مدرسه دولتی پسرانه در ارومیه": "A public boys' school in Urmia",
    "طراح سایت": "Website Designers",
    "آیدی": "Social Media",
    "روش ما": "Our Approach",
    "ترکیبی از آموزش منظم، فعالیت‌های دانش‌آموزی و فضایی دوستانه برای یادگیری بهتر": "A blend of structured learning, student activities, and a friendly environment.",
    "کتابخانه": "Library",
    "فضایی آرام برای مطالعه، امانت کتاب و رشد اندیشه": "A quiet space for reading, borrowing books, and developing ideas.",
    "اینجا ایده‌ها جان می‌گیرند و قدم‌های کوچک، آینده را می‌سازند.": "Ideas come to life here, and small steps shape the future.",
    "ما یک مدرسه نیستیم؛ یک تیمیم. تیمی برای یادگیری و رشد.": "We are more than a school; we are a team dedicated to learning and growth.",
    "جایی که درس، ایده و حال خوب کنار هم می‌نشینند.": "Where learning, ideas, and positive energy come together.",
    "آینده‌سازان این مرز و بوم": "the future generation",
    "آریو مصلی‌نژاد، خانه یادگیری، دوستی و ساختن آینده است.": "Ario Mosallinejad is a home for learning, friendship, and building the future.",
    "آریو مصلی‌نژاد فقط یک اسم روی سربرگ نیست. یک مدرسه دولتی پسرانه در ارومیه است که با مدیریت دلسوزانه آقای سلاطین و تلاش کادر مجرب، محیطی امن و پویا برای آینده‌سازان این مرز و بوم فراهم کرده است.": "Ario Mosallinejad is more than a name on a letterhead. It is a public boys' school in Urmia, providing a safe and supportive environment through dedicated leadership and the commitment of its experienced staff.",
    'معاون آموزشی': 'Academic Deputy',
    'محمد امین سعیدی و امیرعباس قاسمی': 'Mohammad Amin Saeedi and Amirabbas Ghasemi',
    'مدرسه دولتی پسرانه در ارومیه': "A public boys' school in Urmia",
    'ترکیبی از آموزش منظم، فعالیت\u200cهای دانش\u200cآموزی و فضایی دوستانه برای یادگیری بهتر': 'A blend of structured learning, student activities, and a friendly environment.',
    'فضایی آرام برای مطالعه، امانت کتاب و رشد اندیشه': 'A quiet space for reading, borrowing books, and developing ideas.',
    'متون با موفقیت ذخیره شد.': 'Text was saved successfully.',
    'عنوان و متن خبر را وارد کنید.': 'Please enter both a news title and its content.',
    'لینک تصویر معتبر نیست.': 'The image URL is not valid.',
    'خبر با موفقیت ذخیره و منتشر شد.': 'The news article was published successfully.',
    'اطلاعات کارت معتبر نیست.': 'The card information is invalid.',
    'کارت جدید اضافه شد.': 'The new card was added.',
    'کارت با موفقیت ویرایش شد.': 'The card was updated successfully.',
    'کارت حذف شد.': 'The card was deleted.',
    'نام کاربری باید ۳ تا ۳۲ نویسه و رمز حداقل ۶ نویسه باشد.': 'Username must be 3–32 characters and password must be at least 6 characters.',
    'این نام کاربری از قبل وجود دارد!': 'This username already exists.',
    'کاربر جدید با موفقیت اضافه شد.': 'The new user was added successfully.',
    'شما نمی\u200cتوانید کاربر اصلی (admin) را حذف کنید!': 'You cannot delete the primary administrator (admin).',
    'کاربر حذف شد.': 'The user was deleted.',
    'شما دسترسی به این بخش ندارید.': 'You do not have permission to access this section.',
    'پنل ادمین': 'Admin Panel',
    'جایی برای یادگیری و ساختن آینده': 'A place to learn and shape the future',
    'فضای یادگیری و مدرسه': 'A place for learning and school life',
    'آیدی': 'Social Media',
    'طراح سایت': 'Website Designers',
    'روش ما': 'Our Approach',
    'ما کی هستیم': 'Who We Are',
    'کتابخانه': 'Library',
    'روز دانش\u200cآموز': 'Student Day',
    'گروه هنری و تئاتر': 'Arts & Theatre Group',
    'نشریه دانش\u200cآموزی': 'Student Magazine',
    'المپیاد ورزشی': 'School Sports Tournament',
  };

  const attributeDictionary = {
    "نام کاربری": "Username",
    "نام کاربری جدید": "New username",
    "نام کاربری خود را وارد کنید": "Enter your username",
    "یک نام کاربری انتخاب کنید": "Choose a username",
    "رمز عبور": "Password",
    "یک رمز عبور بسازید": "Create a password",
    "عنوان خبر": "News title",
    "متن خبر": "News content",
    "تاریخ خبر (اختیاری؛ مثلاً ۱۴۰۵/۰۸/۲۹)": "News date (optional, e.g. 2026/11/20)",
    "لینک تصویر خبر (اختیاری)": "News image URL (optional)",
    "متن کامل خبر را بنویسید...": "Write the full news article...",
    "عنوان": "Title",
    "توضیحات": "Description"
  };

  const reverseDictionary = {};
  Object.keys(dictionary).forEach(key => { reverseDictionary[dictionary[key]] = key; });
  const originalNodes = new WeakMap();
  const originalAttrs = new WeakMap();

  function applyLanguage(lang) {
    const english = lang === "en";
    document.documentElement.lang = english ? "en" : "fa";
    document.documentElement.dir = english ? "ltr" : "rtl";
    document.body.dataset.language = lang;
    document.body.classList.toggle("language-english", english);

    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);

    nodes.forEach(node => {
      if (!originalNodes.has(node)) originalNodes.set(node, node.nodeValue);
      const original = originalNodes.get(node);
      const key = original.trim();
      if (!key) return;
      const translated = dictionary[key];
      if (english && translated) {
        node.nodeValue = original.replace(key, translated);
      } else if (!english) {
        node.nodeValue = original.replace(key, reverseDictionary[key] || key);
      }
    });

    document.querySelectorAll("input, textarea, select, button, a, [title], [aria-label]").forEach(el => {
      ["placeholder", "title", "aria-label"].forEach(attr => {
        if (!el.hasAttribute(attr)) return;
        let saved = originalAttrs.get(el);
        if (!saved) { saved = {}; originalAttrs.set(el, saved); }
        if (saved[attr] === undefined) saved[attr] = el.getAttribute(attr);
        const original = saved[attr];
        if (english) el.setAttribute(attr, attributeDictionary[original] || dictionary[original] || original);
        else el.setAttribute(attr, original);
      });
      if (el.tagName === "OPTION" && el.textContent.trim()) {
        if (!originalAttrs.has(el)) originalAttrs.set(el, {});
        const saved = originalAttrs.get(el);
        if (saved.optionText === undefined) saved.optionText = el.textContent;
        const key = saved.optionText.trim();
        if (english && dictionary[key]) el.textContent = dictionary[key];
        if (!english) el.textContent = saved.optionText;
      }
    });

    document.querySelectorAll("[data-language-toggle]").forEach(button => {
      button.textContent = english ? "فارسی" : "English";
      button.setAttribute("aria-label", english ? "Switch to Persian" : "Switch to English");
      button.setAttribute("title", english ? "Switch to Persian" : "Switch to English");
    });

    const baseTitle = document.body.dataset.originalTitle || document.title;
    if (english) {
      document.title = baseTitle
        .replace("ورود به آریو", "Sign In to Ario")
        .replace("مدرسه آریو مصلی‌نژاد", "Ario Mosallinejad School")
        .replace("خانه", "Home")
        .replace("درباره ما", "About Us")
        .replace("کادر مدرسه", "Our Team")
        .replace("فعالیت‌ها", "Activities")
        .replace("اخبار", "News")
        .replace("تماس با ما", "Contact Us")
        .replace("پنل ادمین", "Admin Panel");
    } else {
      document.title = baseTitle;
    }
    document.body.style.direction = english ? "ltr" : "rtl";
  }

  window.toggleArioLanguage = function () {
    const next = document.documentElement.lang === "en" ? "fa" : "en";
    try { localStorage.setItem("ario-language", next); } catch (e) {}
    document.cookie = "ario-language=" + next + "; path=/; max-age=31536000; SameSite=Lax";
    applyLanguage(next);
  };

  document.addEventListener("DOMContentLoaded", function () {
    document.body.dataset.originalTitle = document.title;
    let saved = "fa";
    try { saved = localStorage.getItem("ario-language") || "fa"; } catch (e) {}
    document.cookie = "ario-language=" + saved + "; path=/; max-age=31536000; SameSite=Lax";
    applyLanguage(saved);
  });
})();
</script>

</body>
</html>
"""
# ==========================================
# روت‌های ورود/خروج
# ==========================================
@app.route('/')
def index():
    if 'username' in session: return redirect(url_for('home'))
    return render_template_string(AUTH_HTML, show_register=False)

@app.route('/login', methods=['POST'])
def login():
    user = request.form.get('username', '').strip()
    pw = request.form.get('password', '')
    if not user or not pw:
        return render_template_string(AUTH_HTML, error="نام کاربری و رمز عبور را کامل وارد کنید.", show_register=False)
    data = load_data()

    if user in data['users']:
        stored_password = data['users'][user]['password']
        if isinstance(stored_password, str) and stored_password.startswith(('scrypt:', 'pbkdf2:')):
            password_ok = check_password_hash(stored_password, pw)
        else:
            password_ok = stored_password == pw
            if password_ok:
                data['users'][user]['password'] = generate_password_hash(pw)
                save_data(data)
        if password_ok:
            session.clear()
            session['username'] = user
            session['role'] = data['users'][user]['role']
            return redirect(url_for('home'))
    return render_template_string(AUTH_HTML, error="نام کاربری یا رمز عبور اشتباه است.", show_register=False)

@app.route('/register', methods=['POST'])
def register():
    user = request.form.get('username', '').strip()
    pw = request.form.get('password', '')
    if len(user) < 3 or len(user) > 32 or len(pw) < 6:
        return render_template_string(AUTH_HTML, error="نام کاربری باید ۳ تا ۳۲ نویسه و رمز عبور حداقل ۶ نویسه باشد.", show_register=True)
    data = load_data()

    # چک کردن اینکه کاربر قبلا ساخته نشده باشه
    if user in data['users']:
        return render_template_string(AUTH_HTML, error="این نام کاربری قبلا وجود دارد!", show_register=True)
    
    # ذخیره کاربر جدید در دیتابیس
    data['users'][user] = {"password": generate_password_hash(pw), "role": "دانش‌آموز"}
    save_data(data)
    
    # پیام موفقیت
    return render_template_string(AUTH_HTML, success="ثبت‌نام موفق! حالا با همین اطلاعات وارد شوید.", show_register=False)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# ==========================================
# صفحات سایت
# ==========================================
@app.route('/home')
def home():
    if 'username' not in session: return redirect(url_for('index'))
    data = load_data()
    cards = data['sections'].get('home', [])
    card_images = [
        'https://images.unsplash.com/photo-1509062522246-3755977927d7?auto=format&fit=crop&w=900&q=85',
        'https://images.unsplash.com/photo-1529390079861-591de354faf5?auto=format&fit=crop&w=900&q=85',
        'https://images.unsplash.com/photo-1498243691581-b145c3f54a5a?auto=format&fit=crop&w=900&q=85',
        'https://images.unsplash.com/photo-1503676260728-1c00da094a0b?auto=format&fit=crop&w=900&q=85'
    ]
    cards_html = ''.join(
        f'<article class="editorial-card" data-reveal><div class="editorial-card-image" style="background-image:url(\'{card_images[i % len(card_images)]}\')"></div><div class="editorial-card-body"><i class="fas {safe_html(c.get("icon", "fa-star"))}"></i><h3>{safe_html(localized_value(c, "title", ""))}</h3><p>{safe_html(localized_value(c, "text", ""))}</p></div></article>'
        for i, c in enumerate(cards)
    )
    title_text = safe_html(localized_value(data['settings'], 'home_title', 'جایی برای یادگیری و ساختن آینده'))
    subtitle_text = safe_html(localized_value(data['settings'], 'home_subtitle', 'اینجا ایده‌ها جان می‌گیرند و قدم‌های کوچک، آینده را می‌سازند.'))
    staff_count = len(data['sections'].get('staff', []))
    activity_count = len(data['sections'].get('activities', []))
    news_count = len(data['sections'].get('news', []))
    content = f"""
    <main class="signature-home">
      <section class="signature-hero">
        <div class="hero-photo" role="img" aria-label="فضای یادگیری و مدرسه"></div>
        <div class="hero-shade"></div>
        <div class="hero-grain"></div>
        <div class="hero-content" data-reveal>
          <div class="hero-overline"><span class="overline-line"></span> مدرسه آریو مصلی‌نژاد <span class="overline-en">URMIA · IRAN</span></div>
          <h1>{title_text}<br><em>آینده را با هم می‌سازیم.</em></h1>
          <p>{subtitle_text}</p>
          <div class="hero-cta"><a href="/activities" class="cta-solid">تجربه‌های آریو <i class="fas fa-arrow-left"></i></a><a href="/about" class="cta-ghost">داستان ما <i class="fas fa-arrow-up-left-from-circle"></i></a></div>
        </div>
        <div class="hero-caption"><span>01 / 04</span><span>یادگیری · دوستی · کشف</span><span class="caption-line"></span></div>
        <div class="hero-scroll">SCROLL TO EXPLORE <i class="fas fa-arrow-down"></i></div>
      </section>
      <section class="intro-strip">
        <div class="intro-label">آریو، فراتر از کلاس درس</div>
        <p>در آریو، هر پرسش دریچه‌ای تازه است؛ با تجربه کردن، همکاری و کشف استعدادها، برای ساختن فردایی روشن‌تر آماده می‌شویم.</p>
      </section>
      <section class="home-stats" aria-label="آمار مدرسه">
        <div><strong>{staff_count:02d}</strong><span>عضو معرفی‌شده کادر</span></div>
        <div><strong>{activity_count:02d}</strong><span>فعالیت دانش‌آموزی</span></div>
        <div><strong>{news_count:02d}</strong><span>خبر و رویداد</span></div>
        <div class="stats-note">A PLACE TO<br><b>GROW</b></div>
      </section>
      <section class="editorial-section">
        <div class="section-heading"><div><span class="section-eyebrow">DISCOVER ARIO</span><h2>اینجا، آریو<br><em>زندگی می‌کند.</em></h2></div><p>اینجا فرصت داریم کنجکاوی کنیم، مهارت‌های تازه بیاموزیم، دوستی بسازیم و توانایی‌هایمان را به دستاورد تبدیل کنیم.</p></div>
        <div class="editorial-grid">{cards_html}</div>
      </section>
      <section class="feature-band">
        <div class="feature-band-image"></div><div class="feature-band-copy"><span class="section-eyebrow">THE NEXT GENERATION</span><h2>کنجکاوی،<br>شروعِ هر اتفاق بزرگ است.</h2><p>یادگیری واقعی با یک پرسش آغاز می‌شود؛ با ایده‌پردازی، تجربه و همکاری ادامه پیدا می‌کند و به ساختن راه‌های تازه می‌رسد.</p><a href="/activities" class="text-link">بیشتر درباره فعالیت‌ها <i class="fas fa-arrow-left"></i></a></div>
      </section>
      <section class="home-bottom-cta"><span>هر روز، یک قدم به سوی آینده‌ای بهتر.</span><a href="/contact">با مدرسه در ارتباط باش <i class="fas fa-arrow-left"></i></a></section>
    </main>
    """
    return render_template_string(BASE_TEMPLATE.replace("{% block content %}{% endblock %}", content).replace("{{ title }}", "خانه").replace("{{ active_page }}", "home"))

@app.route('/about')
def about():
    if 'username' not in session: return redirect(url_for('index'))
    data = load_data()
    about_text = safe_html(localized_value(data['settings'], 'about_text', ''))
    content = f"""
    <main class="inner-page">
      <section class="inner-hero about-hero"><div class="inner-hero-image" style="background-image:url('https://images.unsplash.com/photo-1509062522246-3755977927d7?auto=format&fit=crop&w=1800&q=90')"></div><div class="inner-hero-overlay"></div><div class="inner-hero-copy"><span class="section-eyebrow">OUR STORY · ARIO SCHOOL</span><h1>یک مدرسه؛<br><em>هزاران امکان.</em></h1><p>داستان ما درباره رشد، رفاقت و ساختن فردایی روشن‌تر است.</p></div></section>
      <section class="story-layout"><div class="story-side"><span>01 — ABOUT US</span><h2>آریو را<br>بشناس.</h2></div><div class="story-main"><p class="story-lead">مدرسه، فقط یک ساختمان و چند کلاس نیست؛ جایی است که شخصیت، رویا و آینده شکل می‌گیرد.</p><p>{about_text}</p><p>ما باور داریم هر دانش‌آموز استعداد و مسیر منحصربه‌فرد خودش را دارد. وظیفه ما فراهم کردن فضایی امن، پویا و الهام‌بخش برای کشف این توانایی‌هاست.</p></div></section>
      <section class="values-row"><article><span>01</span><i class="fas fa-lightbulb"></i><h3>کنجکاوی</h3><p>برای پرسیدن، کشف کردن و پیدا کردن پاسخ‌های تازه.</p></article><article><span>02</span><i class="fas fa-people-group"></i><h3>همراهی</h3><p>رشد در کنار یکدیگر و یاد گرفتن از تفاوت‌ها.</p></article><article><span>03</span><i class="fas fa-seedling"></i><h3>پیشرفت</h3><p>قدم‌های کوچک و پیوسته برای ساختن آینده‌ای بهتر.</p></article></section>
    </main>"""
    return render_template_string(BASE_TEMPLATE.replace("{% block content %}{% endblock %}", content).replace("{{ title }}", "درباره ما").replace("{{ active_page }}", "about"))

@app.route('/staff')
def staff_page():
    if 'username' not in session: return redirect(url_for('index'))
    data = load_data()
    staff = data['sections'].get('staff', [])
    cards_html = ''.join(f'<article class="staff-row" data-reveal><div class="staff-row-icon"><i class="fas {safe_html(c.get("icon", "fa-user-tie"))}"></i></div><div class="staff-row-copy"><h3>{safe_html(localized_value(c, "title", ""))}</h3><p>{safe_html(localized_value(c, "text", ""))}</p></div><span class="staff-row-mark">ARIO</span></article>' for c in staff)
    content = f"""<main class="inner-page editorial-inner">
      <section class="inner-hero staff-hero"><div class="inner-hero-image" style="background-image:url('https://images.unsplash.com/photo-1529390079861-591de354faf5?auto=format&fit=crop&w=1800&q=90')"></div><div class="inner-hero-overlay"></div><div class="inner-hero-copy"><span class="section-eyebrow">THE PEOPLE BEHIND ARIO</span><h1>آدم‌های <em>اثرگذار</em><br>آریو.</h1><p>آدم‌هایی که هر روز با دانش، تعهد و همراهی، مسیر رشد را روشن‌تر می‌کنند.</p></div></section>
      <section class="story-layout staff-intro"><div class="story-side"><span>OUR COMMUNITY</span><h2>یک تیم؛<br>یک مسیر.</h2></div><div class="story-main"><p class="story-lead">پشت هر تجربه خوب در مدرسه، آدم‌هایی هستند که با عشق و مسئولیت کار می‌کنند.</p><p>کادر آریو همراه دانش‌آموزان است تا فضایی امن، پویا و الهام‌بخش برای یادگیری و شکوفایی استعدادها شکل بگیرد.</p></div></section>
      <section class="staff-list">{cards_html or '<div class="empty-state">اطلاعات کادر مدرسه هنوز ثبت نشده است.</div>'}</section>
    </main>"""
    return render_template_string(BASE_TEMPLATE.replace("{% block content %}{% endblock %}", content).replace("{{ title }}", "کادر مدرسه").replace("{{ active_page }}", "staff"))

@app.route('/activities')
def activities_page():
    if 'username' not in session: return redirect(url_for('index'))
    data = load_data()
    activities = data['sections'].get('activities', [])
    photos = ['https://images.unsplash.com/photo-1529390079861-591de354faf5?auto=format&fit=crop&w=1000&q=85','https://images.unsplash.com/photo-1517486808906-6ca8b3f04846?auto=format&fit=crop&w=1000&q=85','https://images.unsplash.com/photo-1523580494863-6f3031224c94?auto=format&fit=crop&w=1000&q=85','https://images.unsplash.com/photo-1503676260728-1c00da094a0b?auto=format&fit=crop&w=1000&q=85']
    cards_html = ''.join(f'<article class="experience-row" data-reveal><div class="experience-photo" style="background-image:url(\'{photos[i%len(photos)]}\')"></div><div class="experience-copy"><span>تجربه آریو</span><h3>{safe_html(localized_value(c, "title", ""))}</h3><p>{safe_html(localized_value(c, "text", ""))}</p></div><div class="experience-icon"><i class="fas {safe_html(c.get("icon", "fa-star"))}"></i></div></article>' for i,c in enumerate(activities))
    content = f"""<main class="inner-page editorial-inner">
      <section class="inner-hero activities-hero"><div class="inner-hero-image" style="background-image:url('https://images.unsplash.com/photo-1529390079861-591de354faf5?auto=format&fit=crop&w=1800&q=90')"></div><div class="inner-hero-overlay"></div><div class="inner-hero-copy"><span class="section-eyebrow">LEARN BY DOING</span><h1>کلاس درس،<br><em>تمام ماجرا نیست.</em></h1><p>ایده‌ها وقتی زنده می‌شوند که آن‌ها را تجربه کنیم.</p></div></section>
      <section class="story-layout"><div class="story-side"><span>DISCOVER · CREATE · GROW</span><h2>یادگیری<br>در جریان است.</h2></div><div class="story-main"><p class="story-lead">هر تجربه، فرصتی برای کشف توانایی‌های تازه است.</p><p>از همکاری و هنر تا فناوری و فعالیت‌های گروهی؛ آریو یادگیری را به تجربه‌ای زنده و ماندگار تبدیل می‌کند.</p></div></section>
      <section class="experience-list">{cards_html or '<div class="empty-state">هنوز فعالیتی ثبت نشده است.</div>'}</section>
    </main>"""
    return render_template_string(BASE_TEMPLATE.replace("{% block content %}{% endblock %}", content).replace("{{ title }}", "فعالیت‌ها").replace("{{ active_page }}", "activities"))

@app.route('/news')
def news_page():
    if 'username' not in session: return redirect(url_for('index'))
    data = load_data()
    items = list(reversed(data['sections'].get('news', [])))
    news_cards = []
    for i,item in enumerate(items):
        image_url = str(item.get('image_url', '')).strip()
        parsed = urlparse(image_url)
        if not (parsed.scheme in ('http','https') and parsed.netloc):
            image_url = ['https://images.unsplash.com/photo-1509062522246-3755977927d7?auto=format&fit=crop&w=1000&q=85','https://images.unsplash.com/photo-1498243691581-b145c3f54a5a?auto=format&fit=crop&w=1000&q=85'][i%2]
        date_html = f'<span class="news-date">{safe_html(item.get("date", "خبر مدرسه"))}</span>'
        news_cards.append(f'<article class="journal-row" data-reveal><div class="journal-photo" style="background-image:url(\'{safe_html(image_url)}\')"></div><div class="journal-copy">{date_html}<h3>{safe_html(localized_value(item, "title", ""))}</h3><p>{safe_html(localized_value(item, "text", ""))}</p></div><span class="journal-arrow"><i class="fas fa-arrow-left"></i></span></article>')
    cards_html = ''.join(news_cards)
    content = f"""<main class="inner-page editorial-inner">
      <section class="inner-hero journal-hero"><div class="inner-hero-image" style="background-image:url('https://images.unsplash.com/photo-1498243691581-b145c3f54a5a?auto=format&fit=crop&w=1800&q=90')"></div><div class="inner-hero-overlay"></div><div class="inner-hero-copy"><span class="section-eyebrow">ARIO JOURNAL · LATEST STORIES</span><h1>روایت روزهای<br><em>پر اتفاق آریو.</em></h1><p>خبرها، لحظه‌ها و اتفاق‌هایی که ارزش به خاطر سپردن دارند.</p></div></section>
      <section class="story-layout"><div class="story-side"><span>ARIO JOURNAL</span><h2>خبرهای<br>مدرسه.</h2></div><div class="story-main"><p class="story-lead">هر روز در آریو داستانی تازه برای گفتن وجود دارد.</p><p>اینجا می‌توانید خبرها، رویدادها و لحظه‌های مهم جامعه مدرسه را دنبال کنید.</p></div></section>
      <section class="journal-list">{cards_html or '<div class="empty-state">هنوز خبری منتشر نشده است. به‌زودی اینجا پر از خبرهای تازه می‌شود.</div>'}</section>
    </main>"""
    return render_template_string(BASE_TEMPLATE.replace("{% block content %}{% endblock %}", content).replace("{{ title }}", "اخبار").replace("{{ active_page }}", "news"))

@app.route('/contact')
def contact():
    if 'username' not in session: return redirect(url_for('index'))
    content = """<main class="inner-page editorial-inner contact-page">
      <section class="inner-hero contact-hero"><div class="inner-hero-image" style="background-image:url('https://images.unsplash.com/photo-1562774053-701939374585?auto=format&fit=crop&w=1800&q=90')"></div><div class="inner-hero-overlay"></div><div class="inner-hero-copy"><span class="section-eyebrow">SAY HELLO TO ARIO</span><h1>راه‌های <em>ارتباط</em><br>با ما.</h1><p>برای پرسش، پیشنهاد یا آشنایی بیشتر، خوشحال می‌شویم صدایتان را بشنویم.</p></div></section>
      <section class="story-layout"><div class="story-side"><span>WE ARE HERE</span><h2>با ما<br>در تماس باش.</h2></div><div class="story-main"><p class="story-lead">ارتباط خوب، شروع یک همکاری ارزشمند است.</p><p>برای دریافت راهنمایی یا مطرح‌کردن پرسش‌هایتان، از راه‌های زیر با مدرسه آریو در ارتباط باشید.</p></div></section>
      <section class="contact-editorial-grid">
        <article class="contact-editorial-item"><span>LOCATION</span><i class="fas fa-location-dot"></i><h3>آدرس مدرسه</h3><p>ارومیه، محله بزرگباش، اول خیابان جانبازان</p><a href="https://maps.google.com/?q=Urmia+Bozorgbash+Janbazan" target="_blank" rel="noopener">باز کردن در نقشه <i class="fas fa-arrow-left"></i></a></article>
        <article class="contact-editorial-item"><span>PHONE</span><i class="fas fa-phone"></i><h3>تلفن تماس</h3><p dir="ltr">۰۴۴-۳۸۶۸۷۶۸۶</p></article>
      </section>
    </main>"""
    return render_template_string(BASE_TEMPLATE.replace("{% block content %}{% endblock %}", content).replace("{{ title }}", "تماس با ما").replace("{{ active_page }}", "contact"))
# ==========================================
# پنل مدیریت (کامل)
# ==========================================
ADMIN_HTML = BASE_TEMPLATE.replace("{% block content %}{% endblock %}", """
<div class="container">
    <h1 class="page-title">پنل مدیریت پیشرفته</h1>
    <div class="hero-card" style="margin-bottom:22px;">مدیریت تمام بخش‌های سایت بدون نیاز به کدنویسی</div>
    <section class="admin-kpi-grid">
      <article><span>کاربران سامانه</span><strong>{{ data.users|length }}</strong><small>حساب‌های ثبت‌شده</small></article>
      <article><span>اعضای کادر</span><strong>{{ data.sections.staff|length }}</strong><small>معرفی‌شده در سایت</small></article>
      <article><span>فعالیت‌ها</span><strong>{{ data.sections.activities|length }}</strong><small>تجربه‌های مدرسه</small></article>
      <article><span>خبرها</span><strong>{{ data.sections.news|length }}</strong><small>مطالب منتشرشده</small></article>
    </section>
    
    {% if msg %}<div style="background: #d1fae5; color: #065f46; padding: 15px; border-radius: 10px; margin-bottom: 20px; text-align: center; font-weight: bold;">{{ msg }}</div>{% endif %}

    <!-- مدیریت کاربران -->
    <div class="admin-section" style="border: 2px solid #3b82f6;">
        <h3><i class="fas fa-users-cog"></i> مدیریت کاربران (ادمین‌ها و معلم‌ها)</h3>
        <form action="/admin/add_user" method="POST" class="admin-form">
            <input type="text" name="username" placeholder="نام کاربری جدید" required style="flex: 1;">
            <input type="password" name="password" placeholder="رمز عبور" required style="flex: 1;">
            <select name="role" style="flex: 1;">
                <option value="مدیر سایت (شما)">مدیر سایت (شما)</option>
                <option value="مدیر مدرسه">مدیر مدرسه</option>
                <option value="معلم">معلم</option>
                <option value="دانش‌آموز">دانش‌آموز</option>
            </select>
            <button type="submit" class="btn-success">افزودن کاربر</button>
        </form>
        
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 10px;">
            {% for uname, uinfo in data.users.items() %}
            <div class="admin-list-item" style="margin-bottom: 0;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <i class="fas fa-user-circle" style="color: #3b82f6; font-size: 1.2rem;"></i>
                    <div>
                        <strong style="display: block;">{{ uname }}</strong>
                        <span style="font-size: 0.8rem; color: #64748b;">{{ uinfo.role }}</span>
                    </div>
                </div>
                {% if uname != 'admin' %}
                <form action="/admin/delete_user/{{ uname }}" method="POST" onsubmit="return confirm('مطمئنی می‌خوای این کاربر رو حذف کنی؟')"><button type="submit" class="btn-danger">حذف</button></form>
                {% else %}
                <span style="font-size: 0.7rem; color: #10b981; font-weight: bold;">اصلی</span>
                {% endif %}
            </div>
            {% endfor %}
        </div>
    </div>

    <!-- ویرایش متن‌های اصلی -->
    <div class="admin-section">
        <h3><i class="fas fa-edit"></i> ویرایش متن‌های اصلی</h3>
        <form action="/admin/update_texts" method="POST">
            <div class="form-group"><label>عنوان بزرگ صفحه خانه / English heading</label><input type="text" name="home_title" value="{{ data.settings.home_title }}" required><input type="text" name="home_title_en" value="{{ data.settings.home_title_en or '' }}" placeholder="English homepage heading" dir="ltr"></div>
            <div class="form-group"><label>متن زیر عنوان صفحه خانه / English subtitle</label><textarea name="home_subtitle" rows="2" required>{{ data.settings.home_subtitle }}</textarea><textarea name="home_subtitle_en" rows="2" placeholder="English homepage subtitle" dir="ltr">{{ data.settings.home_subtitle_en or '' }}</textarea></div>
            <div class="form-group"><label>متن صفحه درباره ما / English about text</label><textarea name="about_text" rows="3" required>{{ data.settings.about_text }}</textarea><textarea name="about_text_en" rows="3" placeholder="English about text" dir="ltr">{{ data.settings.about_text_en or '' }}</textarea></div>
            <button type="submit" class="btn-success"><i class="fas fa-save"></i> ذخیره متون</button>
        </form>
    </div>

    <!-- انتشار خبر مستقل -->
    <div class="admin-section">
        <h3><i class="fas fa-newspaper"></i> انتشار خبر جدید</h3>
        <p style="color:#64748b;margin:8px 0 16px">خبر پس از ذخیره در صفحه «اخبار» نمایش داده می‌شود و با خروج از حساب حذف نخواهد شد.</p>
        <form action="/admin/add_news" method="POST" class="admin-form">
            <input type="text" name="title" placeholder="عنوان خبر (فارسی)" required maxlength="160" style="flex:2;min-width:220px">
            <input type="text" name="title_en" placeholder="English news title" maxlength="160" dir="ltr" style="flex:2;min-width:220px">
            <input type="text" name="date" placeholder="تاریخ خبر (اختیاری؛ مثلاً ۱۴۰۵/۰۸/۲۹)" style="flex:1;min-width:190px">
            <input type="url" name="image_url" placeholder="لینک تصویر خبر (اختیاری)" style="flex:2;min-width:220px">
            <textarea name="text" placeholder="متن کامل خبر را بنویسید..." rows="4" required maxlength="10000" style="flex:1 1 100%;width:100%"></textarea>
            <textarea name="text_en" placeholder="Write the full news article in English..." rows="4" maxlength="10000" dir="ltr" style="flex:1 1 100%;width:100%"></textarea>
            <button type="submit" class="btn-success"><i class="fas fa-save"></i> ذخیره و انتشار خبر</button>
        </form>
    </div>

    <!-- مدیریت کارت‌ها (اضافه کردن) -->
    <div class="admin-section">
        <h3><i class="fas fa-plus-circle"></i> افزودن کارت جدید به هر بخش</h3>
        <form action="/admin/add_card" method="POST" class="admin-form">
            <select name="section" style="flex: 1;">
                <option value="home">صفحه خانه</option>
                <option value="staff">کادر مدرسه</option>
                <option value="activities">فعالیت‌ها</option>
                <option value="news">اخبار</option>
                </select>
            <input type="text" name="title" placeholder="عنوان فارسی" required style="flex: 2;">
            <input type="text" name="title_en" placeholder="English title" dir="ltr" style="flex: 2;">
            <input type="text" name="text" placeholder="توضیحات فارسی" required style="flex: 2;">
            <input type="text" name="text_en" placeholder="English description" dir="ltr" style="flex: 2;">
            <select name="icon" style="flex: 1;">
                <option value="fa-user-tie">مدیر</option>
                <option value="fa-user-graduate">معاون</option>
                <option value="fa-star">ستاره</option>
                <option value="fa-laptop-code">کامپیوتر</option>
                <option value="fa-book">کتاب</option>
                <option value="fa-school">مدرسه</option>
                <option value="fa-trophy">جام</option>
            </select>
            <button type="submit" class="btn-success">افزودن</button>
        </form>
    </div>

    <!-- ویرایش کارت‌ها -->
    {% if edit_card %}
    <div class="admin-section" style="border: 2px solid #f59e0b;">
        <h3 style="color: #d97706;"><i class="fas fa-edit"></i> در حال ویرایش کارت: {{ edit_card.title }}</h3>
        <form action="/admin/edit_card/{{ edit_section }}/{{ edit_index }}" method="POST" class="admin-form">
            <input type="text" name="title" value="{{ edit_card.title }}" required style="flex: 2;">
            <input type="text" name="title_en" value="{{ edit_card.title_en or '' }}" placeholder="English title" dir="ltr" style="flex: 2;">
            <input type="text" name="text" value="{{ edit_card.text }}" required style="flex: 3;">
            <input type="text" name="text_en" value="{{ edit_card.text_en or '' }}" placeholder="English description" dir="ltr" style="flex: 3;">
            <select name="icon" style="flex: 1;">
                <option value="fa-user-tie" {% if edit_card.icon == 'fa-user-tie' %}selected{% endif %}>مدیر</option>
                <option value="fa-user-graduate" {% if edit_card.icon == 'fa-user-graduate' %}selected{% endif %}>معاون</option>
                <option value="fa-star" {% if edit_card.icon == 'fa-star' %}selected{% endif %}>ستاره</option>
                <option value="fa-laptop-code" {% if edit_card.icon == 'fa-laptop-code' %}selected{% endif %}>کامپیوتر</option>
                <option value="fa-book" {% if edit_card.icon == 'fa-book' %}selected{% endif %}>کتاب</option>
                <option value="fa-school" {% if edit_card.icon == 'fa-school' %}selected{% endif %}>مدرسه</option>
                <option value="fa-trophy" {% if edit_card.icon == 'fa-trophy' %}selected{% endif %}>جام</option>
            </select>
            <button type="submit" class="btn-success">ثبت ویرایش</button>
            <a href="/admin" class="btn-danger" style="text-align: center; line-height: 2;">انصراف</a>
        </form>
    </div>
    {% endif %}

    <!-- لیست تمام کارت‌ها -->
    <div class="admin-section">
        <h3><i class="fas fa-list"></i> لیست تمام کارت‌ها</h3>
        <h4 style="margin-top: 20px; color: #3b82f6;">صفحه خانه (Home)</h4>
        {% for card in data.sections.home %}
        <div class="admin-list-item">
            <div style="display: flex; align-items: center; gap: 10px;"><i class="fas {{ card.icon }}"></i> <strong>{{ card.title_en if request.cookies.get("ario-language") == "en" and card.title_en else card.title }}</strong> - <span>{{ card.text_en if request.cookies.get("ario-language") == "en" and card.text_en else card.text }}</span></div>
            <div style="display: flex; gap: 5px;"><a href="/admin?edit_section=home&edit_index={{ loop.index0 }}" class="btn-warning">ویرایش</a><form action="/admin/delete_card/home/{{ loop.index0 }}" method="POST" onsubmit="return confirm('این کارت حذف شود؟')"><button type="submit" class="btn-danger">حذف</button></form></div>
        </div>
        {% endfor %}
        <h4 style="margin-top: 20px; color: #3b82f6;">کادر مدرسه (Staff)</h4>
        {% for card in data.sections.staff %}
        <div class="admin-list-item">
            <div style="display: flex; align-items: center; gap: 10px;"><i class="fas {{ card.icon }}"></i> <strong>{{ card.title_en if request.cookies.get("ario-language") == "en" and card.title_en else card.title }}</strong> - <span>{{ card.text_en if request.cookies.get("ario-language") == "en" and card.text_en else card.text }}</span></div>
            <div style="display: flex; gap: 5px;"><a href="/admin?edit_section=staff&edit_index={{ loop.index0 }}" class="btn-warning">ویرایش</a><form action="/admin/delete_card/staff/{{ loop.index0 }}" method="POST" onsubmit="return confirm('این کارت حذف شود؟')"><button type="submit" class="btn-danger">حذف</button></form></div>
        </div>
        {% endfor %}
        <h4 style="margin-top: 20px; color: #3b82f6;">فعالیت‌ها (Activities)</h4>
        {% for card in data.sections.activities %}
        <div class="admin-list-item">
            <div style="display: flex; align-items: center; gap: 10px;"><i class="fas {{ card.icon }}"></i> <strong>{{ card.title_en if request.cookies.get("ario-language") == "en" and card.title_en else card.title }}</strong> - <span>{{ card.text_en if request.cookies.get("ario-language") == "en" and card.text_en else card.text }}</span></div>
            <div style="display: flex; gap: 5px;"><a href="/admin?edit_section=activities&edit_index={{ loop.index0 }}" class="btn-warning">ویرایش</a><form action="/admin/delete_card/activities/{{ loop.index0 }}" method="POST" onsubmit="return confirm('این کارت حذف شود؟')"><button type="submit" class="btn-danger">حذف</button></form></div>
        </div>
        {% endfor %}
        <h4 style="margin-top: 20px; color: #3b82f6;">اخبار (News)</h4>
        {% for card in data.sections.news %}
        <div class="admin-list-item">
            <div style="display: flex; align-items: center; gap: 10px;"><i class="fas {{ card.icon }}"></i> <strong>{{ card.title_en if request.cookies.get("ario-language") == "en" and card.title_en else card.title }}</strong> - <span>{{ card.text_en if request.cookies.get("ario-language") == "en" and card.text_en else card.text }}</span></div>
            <div style="display: flex; gap: 5px;"><a href="/admin?edit_section=news&edit_index={{ loop.index0 }}" class="btn-warning">ویرایش</a><form action="/admin/delete_card/news/{{ loop.index0 }}" method="POST" onsubmit="return confirm('این کارت حذف شود؟')"><button type="submit" class="btn-danger">حذف</button></form></div>
        </div>
        {% endfor %}
    </div>
</div>
""")
# ==========================================
# روت‌های پنل مدیریت
# ==========================================
@app.route('/admin')
def admin():
    if 'username' not in session or session.get('role') not in ["مدیر سایت (شما)", "مدیر مدرسه"]:
        return "شما دسترسی به این بخش ندارید. <a href='/home'>بازگشت</a>"
    
    data = load_data()
    msg = request.args.get('msg')
    edit_section = request.args.get('edit_section')
    edit_index = request.args.get('edit_index')
    edit_card = None
    
    if edit_section and edit_index is not None:
        try: edit_card = data['sections'][edit_section][int(edit_index)]
        except: pass

    return render_template_string(ADMIN_HTML, data=data, msg=msg, title="پنل ادمین", active_page="admin", edit_card=edit_card, edit_section=edit_section, edit_index=edit_index)

@app.route('/admin/update_texts', methods=['POST'])
def update_texts():
    if session.get('role') not in ["مدیر سایت (شما)", "مدیر مدرسه"]: return redirect(url_for('home'))
    data = load_data()
    data['settings']['home_title'] = request.form['home_title']
    data['settings']['home_subtitle'] = request.form['home_subtitle']
    data['settings']['about_text'] = request.form['about_text']
    data['settings']['home_title_en'] = request.form.get('home_title_en', '').strip()
    data['settings']['home_subtitle_en'] = request.form.get('home_subtitle_en', '').strip()
    data['settings']['about_text_en'] = request.form.get('about_text_en', '').strip()
    save_data(data)
    return redirect(url_for('admin', msg='متون با موفقیت ذخیره شد.'))

@app.route('/admin/add_news', methods=['POST'])
def add_news():
    if session.get('role') not in ["مدیر سایت (شما)", "مدیر مدرسه"]:
        return redirect(url_for('home'))
    title = request.form.get('title', '').strip()
    body = request.form.get('text', '').strip()
    image_url = request.form.get('image_url', '').strip()
    date = request.form.get('date', '').strip() or datetime.now().strftime('%Y-%m-%d')
    parsed = urlparse(image_url) if image_url else None
    if not title or not body:
        return redirect(url_for('admin', msg='عنوان و متن خبر را وارد کنید.'))
    if image_url and (parsed.scheme not in ('http', 'https') or not parsed.netloc):
        return redirect(url_for('admin', msg='لینک تصویر معتبر نیست.'))
    data = load_data()
    data['sections'].setdefault('news', []).append({
        'title': title, 'text': body, 'icon': 'fa-newspaper',
        'title_en': request.form.get('title_en', '').strip(),
        'text_en': request.form.get('text_en', '').strip(),
        'date': date, 'image_url': image_url
    })
    save_data(data)
    return redirect(url_for('admin', msg='خبر با موفقیت ذخیره و منتشر شد.'))


@app.route('/admin/add_card', methods=['POST'])
def add_card():
    if session.get('role') not in ["مدیر سایت (شما)", "مدیر مدرسه"]: return redirect(url_for('home'))
    data = load_data()
    sec = request.form.get('section', '')
    title = request.form.get('title', '').strip()
    text = request.form.get('text', '').strip()
    icon = request.form.get('icon', 'fa-star').strip()
    if sec not in ['home', 'staff', 'activities', 'news'] or not title or not text:
        return redirect(url_for('admin', msg='اطلاعات کارت معتبر نیست.'))
    new_card = {
        "title": title, "text": text, "icon": icon,
        "title_en": request.form.get('title_en', '').strip(),
        "text_en": request.form.get('text_en', '').strip()
    }
    data['sections'][sec].append(new_card)
    save_data(data)
    return redirect(url_for('admin', msg='کارت جدید اضافه شد.'))

@app.route('/admin/edit_card/<section>/<int:index>', methods=['POST'])
def edit_card(section, index):
    if session.get('role') not in ["مدیر سایت (شما)", "مدیر مدرسه"]: return redirect(url_for('home'))
    data = load_data()
    if section in data.get('sections', {}) and 0 <= index < len(data['sections'][section]):
        data['sections'][section][index]['title'] = request.form['title']
        data['sections'][section][index]['text'] = request.form['text']
        data['sections'][section][index]['title_en'] = request.form.get('title_en', '').strip()
        data['sections'][section][index]['text_en'] = request.form.get('text_en', '').strip()
        data['sections'][section][index]['icon'] = request.form['icon']
        save_data(data)
    return redirect(url_for('admin', msg='کارت با موفقیت ویرایش شد.'))

@app.route('/admin/delete_card/<section>/<int:index>', methods=['POST'])
def delete_card(section, index):
    if session.get('role') not in ["مدیر سایت (شما)", "مدیر مدرسه"]: return redirect(url_for('home'))
    data = load_data()
    if section in data.get('sections', {}) and 0 <= index < len(data['sections'][section]):
        data['sections'][section].pop(index)
        save_data(data)
    return redirect(url_for('admin', msg='کارت حذف شد.'))

@app.route('/admin/add_user', methods=['POST'])
def add_user():
    if session.get('role') not in ["مدیر سایت (شما)", "مدیر مدرسه"]: return redirect(url_for('home'))
    data = load_data()
    uname = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    role = request.form.get('role', 'دانش‌آموز')
    if len(uname) < 3 or len(uname) > 32 or len(password) < 6:
        return redirect(url_for('admin', msg='نام کاربری باید ۳ تا ۳۲ نویسه و رمز حداقل ۶ نویسه باشد.'))
    if uname in data['users']:
        return redirect(url_for('admin', msg='این نام کاربری از قبل وجود دارد!'))
    
    data['users'][uname] = {"password": generate_password_hash(password), "role": role}
    save_data(data)
    return redirect(url_for('admin', msg='کاربر جدید با موفقیت اضافه شد.'))

@app.route('/admin/delete_user/<username>', methods=['POST'])
def delete_user(username):
    if session.get('role') not in ["مدیر سایت (شما)", "مدیر مدرسه"]: return redirect(url_for('home'))
    if username == 'admin':
        return redirect(url_for('admin', msg='شما نمی‌توانید کاربر اصلی (admin) را حذف کنید!'))
    
    data = load_data()
    if username in data['users']:
        del data['users'][username]
        save_data(data)
    return redirect(url_for('admin', msg='کاربر حذف شد.'))



# ==========================================
# اجرای برنامه (مخصوص رندر و لوکال)
# ==========================================
if __name__ == '__main__':
    if app.secret_key == 'CHANGE-THIS-SECRET-KEY-BEFORE-DEPLOYMENT':
        print('WARNING: Set a strong SECRET_KEY environment variable before public deployment.')
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
