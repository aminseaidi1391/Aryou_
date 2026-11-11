import os
from flask import Flask, render_template_string, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'super_secret_key_123'

database_url = os.environ.get('DATABASE_URL', 'sqlite:///site.db')
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql+psycopg2://", 1)
elif database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+psycopg2://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url

app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'static', 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    name = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class SiteContent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False)

class Card(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    page_name = db.Column(db.String(50), nullable=False)
    icon = db.Column(db.String(10), default='📌')
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
with app.app_context():
    db.create_all()
    
    if not User.query.filter_by(email='admin@site.com').first():
        admin = User(email='admin@site.com', name='مدیر کل', password=generate_password_hash('123456'), is_admin=True)
        db.session.add(admin)
        db.session.commit()
    
    if not SiteContent.query.first():
        defaults = {
            'home_title': 'جایی که درس، ایده و حال خوب کنار هم می‌نشینند.',
            'home_text': 'ما یک مدرسه نیستیم؛ یک تیمیم. تیمی از دانش‌آموزان کنجکاو، دبیرهای پایه‌کار و کادری که با عشق و تلاش، مدرسه را به جای بهتری برای رشد و شکوفایی تبدیل می‌کنند.',
            'home_img': '', 
            'about_title': 'درباره مدرسه',
            'about_text': 'آریو مصلی‌نژاد فقط یک اسم روی سربرگ نیست. یک مدرسه دولتی پسرانه در ارومیه است که با مدیریت دلسوزانه آقای سلاطین و تلاش کادر مجرب، محیطی امن و پویا برای آینده‌سازان این مرز و بوم فراهم کرده است.',
            'about_img': '', 
            'staff_title': 'کادر مدرسه',
            'staff_text': 'کادری خلاق، پرانرژی و دلسوز که با مدیریت آقای سلاطین و همراهی آقای الوانی، هر روز یک روز به‌یادماندنی برای دانش‌آموزان می‌سازند.',
            'staff_img': '', 
            'act_title': 'فعالیت‌های آموزشی',
            'act_text': 'درس که تمام می‌شود، آریو تازه شروع می‌شود.',
            'act_img': '', 
            'contact_title': 'تماس با ما',
            'contact_text': 'حرف داری؟ زنگ بزن یا سر بزن.',
            'contact_img': '', 
            'contact_address_text': 'ارومیه، محله بازار باش، میدان جانبازان',
            'contact_address_link': 'https://www.google.com/maps/search/?api=1&query=Urmia+Bazaar+Bash+Janbazan+Square',
            'contact_phone': '۰۴۴-۳۸۶۸۷۶۸۶',
            'news_title': 'اخبار مدرسه',
            'news_text': 'به‌زودی اخبار جدید مدرسه در این صفحه قرار می‌گیرد.',
            'news_img': ''
        }
        for key, val in defaults.items(): 
            db.session.add(SiteContent(key=key, value=val))
        db.session.commit()
    
    if not Card.query.first():
        cards = [
            Card(page_name='home', icon='📚', title='روش ما', content='ترکیبی از آموزش منظم، فعالیت‌های دانش‌آموزی و فضایی دوستانه برای یادگیری بهتر.'),
            Card(page_name='home', icon='🏫', title='ما کی هستیم', content='مدرسه دولتی پسرانه در ارومیه.'),
            Card(page_name='home', icon='💻', title='طراح سایت', content='محمد امیر سعیدی و امیرعباس قاسمی\nآیدی ایتا: @amin_Hr\nآیدی روبیکا: @AMINHANDALA\n@xode_Griffin'),
            Card(page_name='home', icon='💻', title='طراح سایت', content='محمد امیر سعیدی و امیرعباس قاسمی\nآیدی ایتا: @amin_Hr\nآیدی روبیکا: @AMINHANDALA\n@'),
            Card(page_name='about', icon='🏫', title='تاریخچه مدرسه', content='مدرسه ما با سال‌ها تجربه در زمینه آموزش و پرورش، همواره در تلاش بوده تا محیطی پویا و با نشاط برای دانش‌آموزان فراهم کند.'),
            Card(page_name='about', icon='🎯', title='اهداف ما', content='تربیت نسلی پویا، خلاق و متعهد برای ساختن آینده‌ای روشن‌تر.'),
            Card(page_name='about', icon='🌟', title='جای خالی شما', content='این کادر می‌تواند به دستان شما پر شود...'),
            Card(page_name='staff', icon='👨‍🏫', title='جناب آقای سلاطین', content='مدیر مدرسه'),
            Card(page_name='staff', icon='👨‍💼', title='جناب آقای الوانی', content='معاون آموزشی'),
            Card(page_name='act', icon='🏆', title='المپیاد ورزشی', content='رقابت سالم و پرنشاط بین کلاس‌ها.'),
            Card(page_name='act', icon='📰', title='نشریه دانش‌آموزی', content='قلم و ایده دانش‌آموزان در قالب نشریه.'),
            Card(page_name='act', icon='🎭', title='گروه هنری و تئاتر', content='اجرای نمایش‌های زیبا در مناسبت‌های مختلف.'),
            Card(page_name='act', icon='🚌', title='اردوهای علمی', content='یادگیری خارج از کلاس درس.'),
            Card(page_name='news', icon='📢', title='اطلاعیه ثبت‌نام', content='ثبت‌نام کلاس‌های تابستانی آغاز شد.'),
            Card(page_name='news', icon='🎉', title='روز دانش‌آموز', content='روز دانش‌آموز، روز تجلیل از آینده‌سازان این مرز و بوم است. در این روز، مراسم ویژه‌ای با حضور دانش‌آموزان و کادر مدرسه برگزار شد.')
        ]
        for c in cards: 
            db.session.add(c)
        db.session.commit()
        BASE_HTML = """
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>مدرسه آریو مصلی‌نژاد</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@300;400;700;900&display=swap');
        body { font-family: 'Vazirmatn', sans-serif; background: #f1f5f9; color: #334155; margin: 0; padding: 0; line-height: 1.8; }
        .navbar { background: #ffffff; box-shadow: 0 2px 10px rgba(0,0,0,0.05); padding: 15px 50px; display: flex; justify-content: space-between; align-items: center; position: sticky; top: 0; z-index: 100; }
        .logo-area { display: flex; align-items: center; gap: 10px; font-weight: 900; color: #1e3a8a; font-size: 20px; }
        .logo-icon { background: #3b82f6; color: white; width: 40px; height: 40px; display: flex; justify-content: center; align-items: center; border-radius: 10px; font-size: 24px; }
        .nav-links { display: flex; gap: 10px; }
        .nav-links a { text-decoration: none; color: #475569; padding: 8px 16px; border-radius: 8px; font-weight: 700; transition: all 0.3s ease; background: #f8fafc; }
        .nav-links a:hover, .nav-links a.active { background: #3b82f6; color: white; box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4); transform: translateY(-2px); }
        .hero { background: linear-gradient(135deg, #bfdbfe, #93c5fd); color: #0f172a; text-align: center; padding: 80px 20px; border-radius: 30px; margin: 30px 20px; box-shadow: 0 15px 30px rgba(59, 130, 246, 0.2); border: 1px solid #60a5fa; }
        .hero h1 { font-size: 40px; margin-bottom: 20px; font-weight: 900; color: #1e3a8a; text-shadow: 1px 1px 2px rgba(255,255,255,0.5);}
        .hero p { font-size: 18px; max-width: 800px; margin: 0 auto 30px auto; opacity: 0.9; color: #1e293b;}
        .hero-img { width: 100%; max-width: 600px; border-radius: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.15); margin-bottom: 30px; object-fit: cover; }
        .container { max-width: 1000px; margin: 0 auto 50px auto; padding: 0 20px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 25px; margin-top: 30px; }
        .card { background: white; padding: 30px; border-radius: 20px; box-shadow: 0 5px 20px rgba(0,0,0,0.05); text-align: center; transition: 0.3s; border-bottom: 4px solid transparent; }
        .card:hover { transform: translateY(-5px); box-shadow: 0 15px 40px rgba(0,0,0,0.1); border-bottom-color: #3b82f6; }
        .card-icon { font-size: 40px; margin-bottom: 15px; }
        .card h3 { color: #1e3a8a; margin-bottom: 10px; }
        .btn { background: #3b82f6; color: white; padding: 12px 30px; border: none; border-radius: 30px; font-weight: bold; cursor: pointer; text-decoration: none; display: inline-block; transition: 0.3s; font-family: inherit; font-size: 16px;}
        .btn:hover { background: #2563eb; transform: scale(1.05); box-shadow: 0 5px 15px rgba(37, 99, 235, 0.3);}
        input[type="text"], input[type="email"], input[type="password"], textarea { width: 100%; padding: 15px; margin-bottom: 15px; border: 1px solid #cbd5e1; border-radius: 10px; font-family: inherit; box-sizing: border-box; background: #f8fafc; }
        input:focus, textarea:focus { outline: none; border-color: #3b82f6; box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2); background: white;}
        .alert { background: #fee2e2; color: #b91c1c; padding: 15px; border-radius: 10px; margin-bottom: 20px; text-align: center; font-weight: bold;}
        @media (max-width: 768px) { 
            .navbar { flex-direction: column; padding: 15px 10px; gap: 15px; } 
            .nav-links { flex-wrap: wrap; justify-content: center; } 
            .nav-links a { padding: 6px 12px; font-size: 14px; }
            .hero { margin: 15px 10px; padding: 40px 15px; } 
            .hero h1 { font-size: 26px; } 
            .grid { grid-template-columns: 1fr; } 
        }
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="logo-area">
            <div class="logo-icon">آ</div>
            <div>آریو مصلی‌نژاد<br><span style="font-size: 12px; color: #6b7280; font-weight: normal;">ارومیه • دولتی</span></div>
        </div>
        <div class="nav-links">
            <a href="/">خانه</a>
            <a href="/about">درباره ما</a>
            <a href="/staff">کادر مدرسه</a>
            <a href="/activities">فعالیت‌ها</a>
            <a href="/news">اخبار</a>
            <a href="/contact">تماس</a>
            {% if current_user.is_authenticated and current_user.is_admin %}
                <a href="/admin" style="color: #ef4444;">⚙️ پنل مدیریت</a>
            {% endif %}
            {% if current_user.is_authenticated %}
                <a href="/logout" style="color: #f59e0b;">خروج ({{ current_user.name }})</a>
            {% else %}
                <a href="/login" style="color: #2563eb;">ورود / ثبت‌نام</a>
            {% endif %}
        </div>
    </nav>
    
    <div class="container">
        {% with messages = get_flashed_messages() %}
            {% if messages %}
                {% for message in messages %}
                    <div class="alert">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
    </div>
    {{ content | safe }}
</body>
</html>
"""
def get_content(key, default=""):
    entry = SiteContent.query.filter_by(key=key).first()
    return entry.value if entry else default

def render_page(title_key, text_key, img_key, page_name):
    title, text, img = get_content(title_key), get_content(text_key), get_content(img_key)
    img_html = f'<img src="/static/uploads/{img}" class="hero-img">' if img else ""
    cards = Card.query.filter_by(page_name=page_name).all()
    cards_html = "".join([f'<div class="card"><div class="card-icon">{c.icon}</div><h3>{c.title}</h3><p>{c.content.replace(chr(10), "<br>")}</p></div>' for c in cards])
    content = f'<div class="hero">{img_html}<h1>{title}</h1><p>{text}</p></div><div class="container"><div class="grid">{cards_html}</div></div>'
    return render_template_string(BASE_HTML, content=content)

@app.route('/')
def home(): return render_page('home_title', 'home_text', 'home_img', 'home')

@app.route('/about')
def about(): return render_page('about_title', 'about_text', 'about_img', 'about')

@app.route('/staff')
def staff(): return render_page('staff_title', 'staff_text', 'staff_img', 'staff')

@app.route('/activities')
def activities(): return render_page('act_title', 'act_text', 'act_img', 'act')

@app.route('/news')
def news(): return render_page('news_title', 'news_text', 'news_img', 'news')

@app.route('/contact')
def contact():
    title, text, img = get_content('contact_title'), get_content('contact_text'), get_content('contact_img')
    img_html = f'<img src="/static/uploads/{img}" class="hero-img">' if img else ""
    content = f'<div class="hero">{img_html}<h1>{title}</h1><p>{text}</p></div><div class="container"><div class="grid"><div class="card"><div class="card-icon">📞</div><h3>تلفن</h3><p dir="ltr" style="font-weight: bold; font-size: 20px;">{get_content("contact_phone")}</p></div><div class="card"><div class="card-icon">📍</div><h3>آدرس</h3><p>{get_content("contact_address_text")}</p><a href="{get_content("contact_address_link")}" target="_blank" class="btn" style="margin-top: 15px; font-size: 14px; padding: 10px 20px;">مشاهده در نقشه</a></div></div></div>'
    return render_template_string(BASE_HTML, content=content)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form.get('email')).first()
        if user and check_password_hash(user.password, request.form.get('password')):
            login_user(user); return redirect(url_for('home'))
        flash('ایمیل یا رمز اشتباه است.')
    content = '<div style="max-width: 400px; margin: 50px auto; background: white; padding: 30px; border-radius: 15px; box-shadow: 0 10px 20px rgba(0,0,0,0.1);"><h2 style="text-align: center; color: #1e3a8a;">ورود</h2><form method="POST"><input type="email" name="email" placeholder="ایمیل" required><input type="password" name="password" placeholder="رمز عبور" required><button type="submit" class="btn" style="width: 100%;">ورود</button></form><p style="text-align: center; margin-top: 15px;">حساب ندارید؟ <a href="/register" style="color: #2563eb;">ثبت‌نام</a></p></div>'
    return render_template_string(BASE_HTML, content=content)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        if User.query.filter_by(email=request.form.get('email')).first(): flash('این ایمیل ثبت شده است')
        else:
            new_user = User(email=request.form.get('email'), name=request.form.get('name'), password=generate_password_hash(request.form.get('password')))
            db.session.add(new_user); db.session.commit()
            flash('ثبت‌نام موفق!'); return redirect(url_for('login'))
    content = '<div style="max-width: 400px; margin: 50px auto; background: white; padding: 30px; border-radius: 15px; box-shadow: 0 10px 20px rgba(0,0,0,0.1);"><h2 style="text-align: center; color: #1e3a8a;">ثبت‌نام</h2><form method="POST"><input type="text" name="name" placeholder="نام" required><input type="email" name="email" placeholder="ایمیل" required><input type="password" name="password" placeholder="رمز عبور" required><button type="submit" class="btn" style="width: 100%;">ثبت‌نام</button></form></div>'
    return render_template_string(BASE_HTML, content=content)

@app.route('/logout')
@login_required
def logout(): logout_user(); return redirect(url_for('home'))

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    if not current_user.is_admin: 
        flash('عدم دسترسی')
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'delete_card':
            Card.query.filter_by(id=request.form.get('card_id')).delete()
            db.session.commit()
            flash('کادر حذف شد!')
        elif action == 'add_card':
            new_card = Card(page_name=request.form.get('card_page'), icon=request.form.get('card_icon'), title=request.form.get('card_title'), content=request.form.get('card_content'))
            db.session.add(new_card)
            db.session.commit()
            flash('کادر جدید اضافه شد!')
        else:
            for key in request.form:
                if key not in ['image_file', 'page_name', 'action']:
                    entry = SiteContent.query.filter_by(key=key).first()
                    if entry: entry.value = request.form.get(key)
                    else: db.session.add(SiteContent(key=key, value=request.form.get(key)))
            file = request.files.get('image_file')
            page = request.form.get('page_name')
            if file and file.filename != '' and page:
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                entry = SiteContent.query.filter_by(key=f"{page}_img").first()
                if entry: entry.value = filename
                else: db.session.add(SiteContent(key=f"{page}_img", value=filename))
                db.session.commit()
            flash('تغییرات متن‌ها ذخیره شد!')
        return redirect(url_for('admin'))
    
    users_html = ""
    for u in User.query.all():
        role_text = "ادمین" if u.is_admin else "کاربر"
        if u.email == 'admin@site.com': action_html = '<span>مدیر کل</span>'
        else:
            btn_color = "#ef4444" if u.is_admin else "#10b981"
            btn_text = "حذف ادمینی" if u.is_admin else "ارتقا به ادمین"
            action_html = f'<a href="/toggle_admin/{u.id}" class="btn" style="padding: 5px 10px; font-size: 12px; background: {btn_color};">{btn_text}</a>'
        users_html += f'<tr><td>{u.name}</td><td>{u.email}</td><td>{role_text}</td><td>{action_html}</td></tr>'
    
    cards_html = ""
    for c in Card.query.all():
        cards_html += f'<tr><td>{c.page_name}</td><td>{c.icon} {c.title}</td><td><form method="POST" style="display:inline;"><input type="hidden" name="card_id" value="{c.id}"><button type="submit" name="action" value="delete_card" class="btn" style="background:#ef4444; padding:5px 10px; font-size:12px;">حذف</button></form></td></tr>'

    content = f"""
    <div style="background: white; padding: 30px; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.08);">
        <h2 style="color: #1e3a8a; text-align: center; margin-bottom: 30px;">پنل مدیریت پیشرفته</h2>
        <div style="text-align: center; margin-bottom: 20px;">
            <button type="button" class="btn tab-btn active" onclick="openTab('home', this)">خانه</button>
            <button type="button" class="btn tab-btn" onclick="openTab('about', this)">درباره ما</button>
            <button type="button" class="btn tab-btn" onclick="openTab('staff', this)">کادر</button>
            <button type="button" class="btn tab-btn" onclick="openTab('act', this)">فعالیت‌ها</button>
            <button type="button" class="btn tab-btn" onclick="openTab('news', this)">اخبار</button>
            <button type="button" class="btn tab-btn" onclick="openTab('contact', this)">تماس</button>
            <button type="button" class="btn tab-btn" onclick="openTab('users', this)">کاربران</button>
            <button type="button" class="btn tab-btn" onclick="openTab('cards', this)">مدیریت کادرها</button>
        </div>
        <form method="POST" enctype="multipart/form-data">
            <input type="hidden" name="page_name" id="current_page" value="home">
            <div id="tab-home" class="page-form active"><input type="text" name="home_title" value="{get_content('home_title')}"><textarea name="home_text" rows="3">{get_content('home_text')}</textarea><input type="file" name="image_file"></div>
            <div id="tab-about" class="page-form" style="display:none;"><input type="text" name="about_title" value="{get_content('about_title')}"><textarea name="about_text" rows="3">{get_content('about_text')}</textarea><input type="file" name="image_file"></div>
            <div id="tab-staff" class="page-form" style="display:none;"><input type="text" name="staff_title" value="{get_content('staff_title')}"><textarea name="staff_text" rows="2">{get_content('staff_text')}</textarea><input type="file" name="image_file"></div>
            <div id="tab-act" class="page-form" style="display:none;"><input type="text" name="act_title" value="{get_content('act_title')}"><textarea name="act_text" rows="3">{get_content('act_text')}</textarea><input type="file" name="image_file"></div>
            <div id="tab-news" class="page-form" style="display:none;"><input type="text" name="news_title" value="{get_content('news_title')}"><textarea name="news_text" rows="3">{get_content('news_text')}</textarea><input type="file" name="image_file"></div>
            <div id="tab-contact" class="page-form" style="display:none;"><input type="text" name="contact_title" value="{get_content('contact_title')}"><textarea name="contact_text" rows="2">{get_content('contact_text')}</textarea><input type="text" name="contact_phone" value="{get_content('contact_phone')}" placeholder="تلفن"><input type="text" name="contact_address_text"
            value="{get_content('contact_address_text')}" placeholder="آدرس"><input type="text" name="contact_address_link" value="{get_content('contact_address_link')}" placeholder="لینک نقشه"><input type="file" name="image_file"></div>
            <div id="tab-users" class="page-form" style="display:none;"><table style="width: 100%; border-collapse: collapse; text-align: center;"><tr style="background: #f1f5f9;"><th>نام</th><th>ایمیل</th><th>نقش</th><th>عملیات</th></tr>{users_html}</table></div>
            <div id="tab-cards" class="page-form" style="display:none;"><h3>کادرهای فعلی</h3><table style="width: 100%; border-collapse: collapse; text-align: center; margin-bottom: 20px;"><tr style="background: #f1f5f9;"><th>صفحه</th><th>عنوان</th><th>عملیات</th></tr>{cards_html}</table><hr style="border: 0; border-top: 1px dashed #cbd5e1; margin: 20px 0;"><h3 style="color: #10b981;">افزودن کادر جدید</h3><select name="card_page" style="padding:10px; margin-bottom:10px; border-radius:8px; width:100%;"><option value="home">خانه</option><option value="about">درباره ما</option><option value="staff">کادر مدرسه</option><option value="act">فعالیت‌ها</option><option value="news">اخبار</option></select><input type="text" name="card_icon" placeholder="آیکون (مثلا 📚)"><input type="text" name="card_title" placeholder="عنوان کادر"><textarea name="card_content" rows="2" placeholder="متن کادر"></textarea><button type="submit" name="action" value="add_card" class="btn" style="background: #10b981; width: 100%;">➕ افزودن کادر</button></div>
            <button type="submit" name="action" value="save_content" class="btn" style="width: 100%; margin-top: 30px; background: #3b82f6;">💾 ذخیره تغییرات متن‌ها</button>
        </form>
    </div>
    <script>
        function openTab(tabName, btn) {{
            document.querySelectorAll('.page-form').forEach(el => el.style.display = 'none');
            document.querySelectorAll('.tab-btn').forEach(el => {{ el.classList.remove('active'); el.style.background = '#cbd5e1'; el.style.color = '#334155'; }});
            document.getElementById('tab-' + tabName).style.display = 'block';
            btn.classList.add('active'); btn.style.background = '#3b82f6'; btn.style.color = 'white';
            document.getElementById('current_page').value = tabName;
        }}
    </script>
    """
    return render_template_string(BASE_HTML, content=content)

@app.route('/toggle_admin/<int:user_id>')
@login_required
def toggle_admin(user_id):
    if not current_user.is_admin: return redirect(url_for('home'))
    user = User.query.get_or_404(user_id)
    if user.email != 'admin@site.com':
        user.is_admin = not user.is_admin; db.session.commit(); flash(f'نقش {user.name} تغییر کرد.')
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
