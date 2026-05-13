from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os
import PyPDF2

app = Flask(__name__)

# إعدادات قاعدة البيانات
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/smart_job_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'

db = SQLAlchemy(app)

# الجداول
class Job(db.Model):
    __tablename__ = 'jobs'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    description = db.Column(db.Text)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(255))
    raw_text = db.Column(db.Text)

# إنشاء الجداول
with app.app_context():
    db.create_all()

# ---------------- ROUTES ----------------

# الصفحة الرئيسية
@app.route('/')
def index():
    return render_template('index.html')

# صفحة التقديم
@app.route('/apply')
def apply_page():
    last_job = Job.query.order_by(Job.id.desc()).first()
    return render_template('apply.html', job=last_job)

# صفحة عرض الوظائف
@app.route('/category')
def category_page():
    return render_template('category_view.html')

@app.route('/category/<cat_name>')
def show_category(cat_name):
    jobs = Job.query.all()
    title = cat_name
    return render_template('category_view.html', title=title, jobs=jobs)




# رفع وتحليل السيرة الذاتية
@app.route('/upload', methods=['POST'])
def upload_file():
    # التحقق من وجود ملف
    if not request.files:
        return "❌ خطأ: لم يتم إرسال ملف."

    file = list(request.files.values())[0]

    if file.filename == '':
        return "❌ خطأ: لم يتم اختيار ملف."

    # حفظ الملف
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filepath)

    # استخراج النص
    text = ""
    try:
        with open(filepath, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() or ""
    except Exception as e:
        text = f"فشل استخراج النص: {str(e)}"

    # حفظ المستخدم
    new_user = User(full_name=file.filename, raw_text=text)
    db.session.add(new_user)
    db.session.commit()

    # المطابقة
    last_job = Job.query.order_by(Job.id.desc()).first()
    score = 0
    if last_job and last_job.description:
      reqs = [r.strip().lower() for r in last_job.description.split(',')]
      found = [skill for skill in reqs if skill in text.lower()]
      score = (len(found) / len(reqs)) * 100 if reqs else 0

      return render_template('result.html', score=score, found=found, job=last_job)

    return "لا توجد وظيفة للمطابقة حالياً"
   
if __name__ == '__main__':
    app.run(debug=True)
