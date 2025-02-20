from flask import Flask, render_template, request, redirect, url_for, session
from models import db, User, Question, Result
from config import Config
import json
import os

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

db_path = os.path.abspath('quiz.db')
print(f"db_path: {db_path}")

with app.app_context():
    db.create_all()
    if Question.query.count() < 10:
        Question.query.delete()
        questions = [
            Question(text="Discord.py ile bir sohbet botu nasıl başlatılır?",
                     options=json.dumps(["Bot(token)", "Client()", "Bot(command_prefix='!')", "discord.Client()"]),
                     correct_answer="Bot(command_prefix='!')"),
            Question(text="Flask ile bir rota nasıl tanımlanır?",
                     options=json.dumps(["@app.route()", "@flask.route()", "app.get()", "route()"]),
                     correct_answer="@app.route()"),
            Question(text="TensorFlow hangi alanda kullanılır?",
                     options=json.dumps(
                         ["Web geliştirme", "Bilgisayar görüşü", "Veritabanı yönetimi", "Oyun geliştirme"]),
                     correct_answer="Bilgisayar görüşü"),
            Question(text="NLP'de BeautifulSoup ne için kullanılır?",
                     options=json.dumps(["Metin tokenizasyonu", "Web kazıma", "Dil modeli eğitimi", "Görüntü işleme"]),
                     correct_answer="Web kazıma"),
            Question(text="NLTK hangi alanda kullanılır?",
                     options=json.dumps(
                         ["Doğal Dil İşleme", "Bilgisayar Görüşü", "Web Geliştirme", "Oyun Programlama"]),
                     correct_answer="Doğal Dil İşleme"),
            Question(text="Discord.py’da bir komut nasıl tanımlanır?",
                     options=json.dumps(
                         ["@bot.command()", "@client.event()", "@discord.command()", "bot.add_command()"]),
                     correct_answer="@bot.command()"),
            Question(text="Flask’ta statik dosyalar hangi klasörde saklanır?",
                     options=json.dumps(["templates", "static", "media", "assets"]),
                     correct_answer="static"),
            Question(text="Yapay zeka modelini eğitmek için hangi kütüphane kullanılır?",
                     options=json.dumps(["Flask", "TensorFlow", "BeautifulSoup", "Discord.py"]),
                     correct_answer="TensorFlow"),
            Question(text="ImageAI ile ne yapılabilir?",
                     options=json.dumps(["Web kazıma", "Görüntü tanıma", "Veritabanı yönetimi", "Metin işleme"]),
                     correct_answer="Görüntü tanıma"),
            Question(text="BeautifulSoup hangi dilde yazılmıştır?",
                     options=json.dumps(["Java", "Python", "C++", "JavaScript"]),
                     correct_answer="Python"),
        ]
        db.session.bulk_save_objects(questions)
        db.session.commit()
        print(f"Veritabanına {Question.query.count()} soru eklendi!")
    else:
        print(f"Veritabanında zaten {Question.query.count()} soru var!")


@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        user = User.query.filter_by(username=username).first()
        if not user:
            user = User(username=username)
            db.session.add(user)
            db.session.commit()
        session['username'] = username
        return redirect(url_for('index'))
    return render_template('index.html')


@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    if 'username' not in session:
        return redirect(url_for('login'))

    all_questions = Question.query.all()
    for q in all_questions:
        q.options_list = json.loads(q.options)

    page = request.args.get('page', 1, type=int)
    per_page = 5
    total_pages = 2

    start = (page - 1) * per_page
    end = start + per_page
    questions = all_questions[start:end]
    print(f"Sayfa {page}: {len(questions)} soru gösteriliyor!")

    if request.method == 'POST':
        if 'answers' not in session:
            session['answers'] = {}

        for question in questions:
            user_answer = request.form.get(f'question_{question.id}')
            if user_answer:
                session['answers'][str(question.id)] = user_answer
                session.modified = True

        if page < total_pages:
            return redirect(url_for('quiz', page=page + 1))
        else:
            score = 0
            for question in all_questions:
                user_answer = session['answers'].get(str(question.id))
                if user_answer == question.correct_answer:
                    score += 1

            user = User.query.filter_by(username=session['username']).first()
            if not user:
                user = User(username=session['username'])
                db.session.add(user)
                db.session.commit()
                print(f"Yeni kullanıcı oluşturuldu: {session['username']}")

            result = Result(user_id=user.id, score=score)
            if score > user.high_score:
                user.high_score = score
            db.session.add(result)
            db.session.commit()

            top_score = db.session.query(db.func.max(User.high_score)).scalar()
            session.pop('answers', None)
            return render_template('result.html', score=score, high_score=user.high_score, top_score=top_score)

    return render_template('quiz.html', questions=questions, page=page, total_pages=total_pages)


@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('answers', None)
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)