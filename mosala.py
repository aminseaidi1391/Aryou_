import json
import os
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
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        # ==========================================
# قالب پایه (تم روشن + ریسپانسیو + افکت شیشه‌ای)
# ==========================================
BASE_TEMPLATE = """
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
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
        <div class="auth-btns">
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
            width:min(1180px,calc(100% - 64px)); min-height:calc(100vh - 125px);
            margin:0 auto; padding:54px 0 62px; display:grid;
            grid-template-columns:1.08fr .92fr; align-items:center; gap:clamp(35px,7vw,100px);
            position:relative; z-index:1;
        }
        .intro { padding:10px 0 20px; }
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
    <header class="topbar">
        <a class="brand" href="/home">
            <div class="brand-mark">آ</div>
            <div class="brand-name">آریو مصلی‌نژاد<small>مدرسه‌ای برای ساختن آینده</small></div>
        </a>
        <nav class="top-links">
            <a href="/home">خانه</a>
            <a href="/about">درباره مدرسه</a>
            <a href="/news">تازه‌ها</a>
            <a class="home-link" href="/home"><i class="fa-solid fa-arrow-up-left-from-circle"></i> بازگشت به سایت</a>
        </nav>
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
                    <h2>خوش برگشتی! 👋</h2>
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
    cards_html = "".join([f'<div class="card"><i class="fas {safe_html(c.get("icon", "fa-star"))}"></i><h3>{safe_html(c.get("title", ""))}</h3><p>{safe_html(c.get("text", ""))}</p></div>' for c in data['sections']['home']])
    
    content = f"""
    <div class="container home-container">
        <div class="home-kicker"><i class="fas fa-sparkles"></i> فضای اختصاصی جامعه آریو</div>
        <h1 class="page-title" style="font-size: 2.5rem; margin-bottom: 20px;">{safe_html(data['settings'].get('home_title', ''))}</h1>
        <div class="hero-card">
            {safe_html(data['settings'].get('home_subtitle', ''))}
        </div>
        <div class="grid-cards">{cards_html}</div>
    </div>
    """
    return render_template_string(BASE_TEMPLATE.replace("{% block content %}{% endblock %}", content).replace("{{ title }}", "خانه").replace("{{ active_page }}", "home"))

@app.route('/about')
def about():
    if 'username' not in session: return redirect(url_for('index'))
    data = load_data()
    content = f"""
    <div class="container">
        <h1 class="page-title">درباره مدرسه</h1>
        <div class="hero-card" style="margin-bottom: 40px;">
            {safe_html(data['settings'].get('about_text', ''))}
        </div>
        <div class="grid-cards">
            <div class="card"><i class="fas fa-bullseye"></i><h3>اهداف ما</h3><p>تربیت نسل پویا، خلاق و متعهد برای ساختن آینده‌ای روشن‌تر.</p></div>
            <div class="card"><i class="fas fa-history"></i><h3>تاریخچه مدرسه</h3><p>مدرسه ما با سال‌ها تجربه در زمینه آموزش و پرورش، همواره در تلاش بوده تا محیطی پویا و با نشاط برای دانش‌آموزان فراهم کند.</p></div>
        </div>
        <p style="text-align: center; margin-top: 40px; color: #64748b; line-height: 1.8;">مدرسه آریو مصلی‌نژاد با تکیه بر کادری مجرب و دلسوز، همواره در تلاش است تا محیطی امن، شاد و پویا برای رشد علمی و اخلاقی دانش‌آموزان فراهم کند. ما معتقدیم که هر دانش‌آموز می‌تواند با تلاش و پشتکار به قله‌های موفقیت دست یابد.</p>
    </div>
    """
    return render_template_string(BASE_TEMPLATE.replace("{% block content %}{% endblock %}", content).replace("{{ title }}", "درباره ما").replace("{{ active_page }}", "about"))

@app.route('/staff')
def staff_page():
    if 'username' not in session: return redirect(url_for('index'))
    data = load_data()
    cards_html = "".join([f'<div class="card"><i class="fas {safe_html(c.get("icon", "fa-user"))}"></i><h3>{safe_html(c.get("title", ""))}</h3><p>{safe_html(c.get("text", ""))}</p></div>' for c in data['sections']['staff']])
    content = f"""
    <div class="container">
        <h1 class="page-title">کادر مدرسه</h1>
        <div class="hero-card">کادری خلاق، پرانرژی و دلسوز که هر روز یک روز به یادماندنی برای دانش‌آموزان می‌سازند.</div>
        <div class="grid-cards">{cards_html}</div>
    </div>
    """
    return render_template_string(BASE_TEMPLATE.replace("{% block content %}{% endblock %}", content).replace("{{ title }}", "کادر مدرسه").replace("{{ active_page }}", "staff"))

@app.route('/activities')
def activities_page():
    if 'username' not in session: return redirect(url_for('index'))
    data = load_data()
    cards_html = "".join([f'<div class="card"><i class="fas {safe_html(c.get("icon", "fa-star"))}"></i><h3>{safe_html(c.get("title", ""))}</h3><p>{safe_html(c.get("text", ""))}</p></div>' for c in data['sections']['activities']])
    content = f"""
    <div class="container">
        <h1 class="page-title">فعالیت‌های آموزشی</h1>
        <div class="hero-card">درس که تمام می‌شود، آریو تازه شروع می‌شود.</div>
        <div class="grid-cards">{cards_html}</div>
    </div>
    """
    return render_template_string(BASE_TEMPLATE.replace("{% block content %}{% endblock %}", content).replace("{{ title }}", "فعالیت‌ها").replace("{{ active_page }}", "activities"))

@app.route('/news')
def news_page():
    if 'username' not in session: return redirect(url_for('index'))
    data = load_data()
    cards_html = "".join([f'<div class="card"><i class="fas {safe_html(c.get("icon", "fa-newspaper"))}"></i><h3>{safe_html(c.get("title", ""))}</h3><p>{safe_html(c.get("text", ""))}</p></div>' for c in data['sections']['news']])
    content = f"""
    <div class="container">
        <h1 class="page-title">اخبار مدرسه</h1>
        <div class="hero-card">به‌زودی اخبار جدید مدرسه در این صفحه قرار می‌گیرد.</div>
        <div class="grid-cards">{cards_html}</div>
    </div>
    """
    return render_template_string(BASE_TEMPLATE.replace("{% block content %}{% endblock %}", content).replace("{{ title }}", "اخبار").replace("{{ active_page }}", "news"))

@app.route('/contact')
def contact():
    if 'username' not in session: return redirect(url_for('index'))
    content = """
    <div class="container">
        <h1 class="page-title">تماس با ما</h1>
        <div class="hero-card">حرف داری؟ زنگ بزن یا سر بزن.</div>
        <div class="grid-cards">
            <div class="card"><i class="fas fa-map-marker-alt"></i><h3>آدرس</h3><p>ارومیه، محله بزرگباش، اول خیابان جان‌بازان</p><a href="https://maps.google.com/?q=Urmia+Bozorgbash+Janbazan" target="_blank" class="btn-map">مشاهده در نقشه</a></div>
            <div class="card"><i class="fas fa-phone-alt"></i><h3>تلفن</h3><p>۰۴۴-۳۸۶۸۷۶۸۶</p></div>
        </div>
    </div>
    """
    return render_template_string(BASE_TEMPLATE.replace("{% block content %}{% endblock %}", content).replace("{{ title }}", "تماس با ما").replace("{{ active_page }}", "contact"))
# ==========================================
# پنل مدیریت (کامل)
# ==========================================
ADMIN_HTML = BASE_TEMPLATE.replace("{% block content %}{% endblock %}", """
<div class="container">
    <h1 class="page-title">پنل مدیریت پیشرفته</h1>
    <div class="hero-card" style="margin-bottom: 30px;">مدیریت تمام بخش‌های سایت بدون نیاز به کدنویسی</div>
    
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
            <div class="form-group"><label>عنوان بزرگ صفحه خانه</label><input type="text" name="home_title" value="{{ data.settings.home_title }}" required></div>
            <div class="form-group"><label>متن زیر عنوان صفحه خانه</label><textarea name="home_subtitle" rows="2" required>{{ data.settings.home_subtitle }}</textarea></div>
            <div class="form-group"><label>متن صفحه درباره ما</label><textarea name="about_text" rows="3" required>{{ data.settings.about_text }}</textarea></div>
            <button type="submit" class="btn-success"><i class="fas fa-save"></i> ذخیره متون</button>
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
            <input type="text" name="title" placeholder="عنوان" required style="flex: 2;">
            <input type="text" name="text" placeholder="توضیحات" required style="flex: 2;">
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
            <input type="text" name="text" value="{{ edit_card.text }}" required style="flex: 3;">
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
            <div style="display: flex; align-items: center; gap: 10px;"><i class="fas {{ card.icon }}"></i> <strong>{{ card.title }}</strong> - <span>{{ card.text }}</span></div>
            <div style="display: flex; gap: 5px;"><a href="/admin?edit_section=home&edit_index={{ loop.index0 }}" class="btn-warning">ویرایش</a><form action="/admin/delete_card/home/{{ loop.index0 }}" method="POST" onsubmit="return confirm('این کارت حذف شود؟')"><button type="submit" class="btn-danger">حذف</button></form></div>
        </div>
        {% endfor %}
        <h4 style="margin-top: 20px; color: #3b82f6;">کادر مدرسه (Staff)</h4>
        {% for card in data.sections.staff %}
        <div class="admin-list-item">
            <div style="display: flex; align-items: center; gap: 10px;"><i class="fas {{ card.icon }}"></i> <strong>{{ card.title }}</strong> - <span>{{ card.text }}</span></div>
            <div style="display: flex; gap: 5px;"><a href="/admin?edit_section=staff&edit_index={{ loop.index0 }}" class="btn-warning">ویرایش</a><form action="/admin/delete_card/staff/{{ loop.index0 }}" method="POST" onsubmit="return confirm('این کارت حذف شود؟')"><button type="submit" class="btn-danger">حذف</button></form></div>
        </div>
        {% endfor %}
        <h4 style="margin-top: 20px; color: #3b82f6;">فعالیت‌ها (Activities)</h4>
        {% for card in data.sections.activities %}
        <div class="admin-list-item">
            <div style="display: flex; align-items: center; gap: 10px;"><i class="fas {{ card.icon }}"></i> <strong>{{ card.title }}</strong> - <span>{{ card.text }}</span></div>
            <div style="display: flex; gap: 5px;"><a href="/admin?edit_section=activities&edit_index={{ loop.index0 }}" class="btn-warning">ویرایش</a><form action="/admin/delete_card/activities/{{ loop.index0 }}" method="POST" onsubmit="return confirm('این کارت حذف شود؟')"><button type="submit" class="btn-danger">حذف</button></form></div>
        </div>
        {% endfor %}
        <h4 style="margin-top: 20px; color: #3b82f6;">اخبار (News)</h4>
        {% for card in data.sections.news %}
        <div class="admin-list-item">
            <div style="display: flex; align-items: center; gap: 10px;"><i class="fas {{ card.icon }}"></i> <strong>{{ card.title }}</strong> - <span>{{ card.text }}</span></div>
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
    save_data(data)
    return redirect(url_for('admin', msg='متون با موفقیت ذخیره شد.'))

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
    new_card = {"title": title, "text": text, "icon": icon}
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
