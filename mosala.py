import json
import os
from flask import Flask, render_template_string, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'super_secret_key_1403'
DATA_FILE = 'school_data.json'

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
</body>
</html>
"""
# ==========================================
# صفحه ورود لاکچری (تیره، ماه و ستاره - کاملاً بهینه برای موبایل)
# ==========================================
AUTH_HTML = """
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>ورود | مدرسه آریو مصلی‌نژاد</title>
    <link href="https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css" rel="stylesheet" type="text/css" />
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Vazirmatn', sans-serif; }
        body { background: #0f172a; min-height: 100vh; min-height: 100dvh; display: flex; justify-content: center; align-items: center; position: relative; overflow-x: hidden; overflow-y: auto; padding: 20px; }
        .glow, .glow2, .stars, .moon, .shooting-star { pointer-events: none; }
        .glow { position: absolute; width: 600px; height: 600px; background: radial-gradient(circle, rgba(79,70,229,0.4) 0%, rgba(15,23,42,0) 70%); top: -200px; left: -200px; border-radius: 50%; animation: pulse 8s infinite alternate; }
        .glow2 { position: absolute; width: 500px; height: 500px; background: radial-gradient(circle, rgba(16,185,129,0.3) 0%, rgba(15,23,42,0) 70%); bottom: -150px; right: -100px; border-radius: 50%; animation: pulse 10s infinite alternate-reverse; }
        @keyframes pulse { 0% { transform: scale(1); opacity: 0.6; } 100% { transform: scale(1.2); opacity: 1; } }
        .stars { position: absolute; top: 0; left: 0; right: 0; bottom: 0; background-image: radial-gradient(1.5px 1.5px at 20px 30px, #fff, rgba(0,0,0,0)), radial-gradient(2px 2px at 40px 70px, #fff, rgba(0,0,0,0)), radial-gradient(1.5px 1.5px at 50px 160px, #fff, rgba(0,0,0,0)), radial-gradient(2px 2px at 90px 40px, #fff, rgba(0,0,0,0)); background-repeat: repeat; background-size: 250px 250px; opacity: 0.5; animation: twinkle 5s infinite alternate; }
        @keyframes twinkle { 0% { opacity: 0.2; } 100% { opacity: 0.7; } }
        .moon { position: absolute; top: 8%; right: 10%; width: 80px; height: 80px; background: #fdf4dc; border-radius: 50%; box-shadow: 0 0 40px 10px rgba(253, 244, 220, 0.3); z-index: 1; }
        .shooting-star { position: absolute; top: 0; left: -100px; width: 100px; height: 2px; background: linear-gradient(90deg, rgba(255,255,255,1), rgba(255,255,255,0)); animation: shoot 4s linear infinite; z-index: 2; opacity: 0; }
        @keyframes shoot { 0% { transform: translateX(0) translateY(0) rotate(45deg); opacity: 1; } 20% { transform: translateX(600px) translateY(600px) rotate(45deg); opacity: 0; } 100% { transform: translateX(600px) translateY(600px) rotate(45deg); opacity: 0; } }
        
        .auth-box { position: relative; z-index: 10; background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.1); padding: 40px 30px; border-radius: 30px; text-align: center; color: #fff; width: 100%; max-width: 400px; box-shadow: 0 30px 60px rgba(0,0,0,0.4); margin: auto; }
        .auth-box h2 { font-size: 1.8rem; margin-bottom: 30px; font-weight: 900; background: linear-gradient(to right, #a5b4fc, #818cf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        
        /* تب‌های ورود و ثبت‌نام */
        .tabs { display: flex; margin-bottom: 25px; background: rgba(0,0,0,0.2); border-radius: 12px; padding: 5px; }
        .tab { flex: 1; padding: 10px; cursor: pointer; color: #94a3b8; transition: 0.3s; font-weight: 700; border-radius: 8px; font-size: 0.95rem; }
        .tab.active { background: #4f46e5; color: #fff; box-shadow: 0 4px 15px rgba(79, 70, 229, 0.4); }
        
        form { display: none; flex-direction: column; gap: 15px; }
        form.active { display: flex; animation: fadeIn 0.4s ease; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        
        .input-group { position: relative; }
        .input-group i { position: absolute; right: 15px; top: 50%; transform: translateY(-50%); color: #64748b; font-size: 1.1rem; }
        input { width: 100%; padding: 14px 45px 14px 15px; border-radius: 12px; border: 2px solid rgba(255,255,255,0.05); background: rgba(0,0,0,0.3); color: #fff; font-family: inherit; outline: none; transition: 0.3s; font-size: 16px; }
        input:focus { border-color: #818cf8; background: rgba(0,0,0,0.5); box-shadow: 0 0 0 3px rgba(129, 140, 248, 0.2); }
        button { background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%); border: none; padding: 15px; border-radius: 12px; color: #fff; font-size: 1.1rem; font-weight: 800; cursor: pointer; transition: 0.3s; margin-top: 10px; font-family: inherit; }
        button:hover { transform: translateY(-2px); box-shadow: 0 10px 20px rgba(79, 70, 229, 0.4); }
        .msg { margin-top: 15px; font-size: 0.9rem; color: #f87171; font-weight: bold; }
    </style>
    <script>
        function switchTab(tabId) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('form').forEach(f => f.classList.remove('active'));
            document.getElementById('tab-' + tabId).classList.add('active');
            document.getElementById('form-' + tabId).classList.add('active');
        }
    </script>
</head>
<body>
    <div class="glow"></div><div class="glow2"></div><div class="stars"></div><div class="moon"></div><div class="shooting-star"></div>
    
    <div class="auth-box">
        <h2>آریو مصلی‌نژاد</h2>
        
        <div class="tabs">
            <div id="tab-login" class="tab active" onclick="switchTab('login')">ورود</div>
            <div id="tab-register" class="tab" onclick="switchTab('register')">ثبت‌نام</div>
        </div>

        <form id="form-login" class="active" action="/login" method="POST">
            <div class="input-group"><i class="fas fa-user"></i><input type="text" name="username" placeholder="نام کاربری" required></div>
            <div class="input-group"><i class="fas fa-lock"></i><input type="password" name="password" placeholder="رمز عبور" required></div>
            <button type="submit">ورود به سامانه</button>
            {% if error %}<div class="msg">{{ error }}</div>{% endif %}
            {% if success %}<div class="msg" style="color: #34d399;">{{ success }}</div>{% endif %}
        </form>

        <form id="form-register" action="/register" method="POST">
            <div class="input-group"><i class="fas fa-user-plus"></i><input type="text" name="username" placeholder="نام کاربری جدید" required></div>
            <div class="input-group"><i class="fas fa-lock"></i><input type="password" name="password" placeholder="رمز عبور" required></div>
            <button type="submit">ساخت حساب کاربری</button>
        </form>
    </div>
</body>
</html>
"""
# ==========================================
# روت‌های ورود/خروج
# ==========================================
@app.route('/')
def index():
    if 'username' in session: return redirect(url_for('home'))
    return render_template_string(AUTH_HTML)

@app.route('/login', methods=['POST'])
def login():
    user = request.form['username'].strip()
    pw = request.form['password'].strip()
    data = load_data()
    
    if user in data['users'] and data['users'][user]['password'] == pw:
        session['username'] = user
        session['role'] = data['users'][user]['role']
        return redirect(url_for('home'))
    return render_template_string(AUTH_HTML, error="نام کاربری یا رمز عبور اشتباه است.")

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
    cards_html = "".join([f'<div class="card"><i class="fas {c.get("icon", "fa-star")}"></i><h3>{c["title"]}</h3><p>{c["text"]}</p></div>' for c in data['sections']['home']])
    
    content = f"""
    <div class="container">
        <h1 class="page-title" style="font-size: 2.5rem; margin-bottom: 20px;">{data['settings']['home_title']}</h1>
        <div class="hero-card">
            {data['settings']['home_subtitle']}
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
            {data['settings']['about_text']}
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
    cards_html = "".join([f'<div class="card"><i class="fas {c.get("icon", "fa-user")}"></i><h3>{c["title"]}</h3><p>{c["text"]}</p></div>' for c in data['sections']['staff']])
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
    cards_html = "".join([f'<div class="card"><i class="fas {c.get("icon", "fa-star")}"></i><h3>{c["title"]}</h3><p>{c["text"]}</p></div>' for c in data['sections']['activities']])
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
    cards_html = "".join([f'<div class="card"><i class="fas {c.get("icon", "fa-newspaper")}"></i><h3>{c["title"]}</h3><p>{c["text"]}</p></div>' for c in data['sections']['news']])
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
                <a href="/admin/delete_user/{{ uname }}" class="btn-danger" onclick="return confirm('مطمئنی می‌خوای این کاربر رو حذف کنی؟')">حذف</a>
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
            <div style="display: flex; gap: 5px;"><a href="/admin?edit_section=home&edit_index={{ loop.index0 }}" class="btn-warning">ویرایش</a><a href="/admin/delete_card/home/{{ loop.index0 }}" class="btn-danger">حذف</a></div>
        </div>
        {% endfor %}
        <h4 style="margin-top: 20px; color: #3b82f6;">کادر مدرسه (Staff)</h4>
        {% for card in data.sections.staff %}
        <div class="admin-list-item">
            <div style="display: flex; align-items: center; gap: 10px;"><i class="fas {{ card.icon }}"></i> <strong>{{ card.title }}</strong> - <span>{{ card.text }}</span></div>
            <div style="display: flex; gap: 5px;"><a href="/admin?edit_section=staff&edit_index={{ loop.index0 }}" class="btn-warning">ویرایش</a><a href="/admin/delete_card/staff/{{ loop.index0 }}" class="btn-danger">حذف</a></div>
        </div>
        {% endfor %}
        <h4 style="margin-top: 20px; color: #3b82f6;">فعالیت‌ها (Activities)</h4>
        {% for card in data.sections.activities %}
        <div class="admin-list-item">
            <div style="display: flex; align-items: center; gap: 10px;"><i class="fas {{ card.icon }}"></i> <strong>{{ card.title }}</strong> - <span>{{ card.text }}</span></div>
            <div style="display: flex; gap: 5px;"><a href="/admin?edit_section=activities&edit_index={{ loop.index0 }}" class="btn-warning">ویرایش</a><a href="/admin/delete_card/activities/{{ loop.index0 }}" class="btn-danger">حذف</a></div>
        </div>
        {% endfor %}
        <h4 style="margin-top: 20px; color: #3b82f6;">اخبار (News)</h4>
        {% for card in data.sections.news %}
        <div class="admin-list-item">
            <div style="display: flex; align-items: center; gap: 10px;"><i class="fas {{ card.icon }}"></i> <strong>{{ card.title }}</strong> - <span>{{ card.text }}</span></div>
            <div style="display: flex; gap: 5px;"><a href="/admin?edit_section=news&edit_index={{ loop.index0 }}" class="btn-warning">ویرایش</a><a href="/admin/delete_card/news/{{ loop.index0 }}" class="btn-danger">حذف</a></div>
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
    sec = request.form['section']
    new_card = {"title": request.form['title'], "text": request.form['text'], "icon": request.form['icon']}
    data['sections'][sec].append(new_card)
    save_data(data)
    return redirect(url_for('admin', msg='کارت جدید اضافه شد.'))

@app.route('/admin/edit_card/<section>/<int:index>', methods=['POST'])
def edit_card(section, index):
    if session.get('role') not in ["مدیر سایت (شما)", "مدیر مدرسه"]: return redirect(url_for('home'))
    data = load_data()
    if 0 <= index < len(data['sections'][section]):
        data['sections'][section][index]['title'] = request.form['title']
        data['sections'][section][index]['text'] = request.form['text']
        data['sections'][section][index]['icon'] = request.form['icon']
        save_data(data)
    return redirect(url_for('admin', msg='کارت با موفقیت ویرایش شد.'))

@app.route('/admin/delete_card/<section>/<int:index>')
def delete_card(section, index):
    if session.get('role') not in ["مدیر سایت (شما)", "مدیر مدرسه"]: return redirect(url_for('home'))
    data = load_data()
    if 0 <= index < len(data['sections'][section]):
        data['sections'][section].pop(index)
        save_data(data)
    return redirect(url_for('admin', msg='کارت حذف شد.'))

@app.route('/admin/add_user', methods=['POST'])
def add_user():
    if session.get('role') not in ["مدیر سایت (شما)", "مدیر مدرسه"]: return redirect(url_for('home'))
    data = load_data()
    uname = request.form['username'].strip()
    if uname in data['users']:
        return redirect(url_for('admin', msg='این نام کاربری از قبل وجود دارد!'))
    
    data['users'][uname] = {"password": request.form['password'], "role": request.form['role']}
    save_data(data)
    return redirect(url_for('admin', msg='کاربر جدید با موفقیت اضافه شد.'))

@app.route('/admin/delete_user/<username>')
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
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
