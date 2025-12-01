import requests
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import re
from datetime import datetime, date
from collections import defaultdict
from flask_login import login_required, current_user

# Dotenvの読み込み（必要に応じて）
import os
from dotenv import load_dotenv
load_dotenv()

# Flaskアプリ設定
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 必ずあなたの秘密鍵を設定してください

GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
TMDB_API_KEY  = os.getenv("TMDB_API_KEY", "")

# DB設定
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Flask-Login設定
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Userモデル


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)
    mbti_type = db.Column(db.String(4), nullable=True)
    city = db.Column(db.String(50), nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Logモデル


class Log(db.Model):
    __tablename__ = 'logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    role = db.Column(db.String(20), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref='logs')


# DB初期化
with app.app_context():
    db.create_all()

# ユーザーロード用


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ログ保存


def insert_log(user_id, message, role):
    log = Log(user_id=user_id, message=message, role=role)
    db.session.add(log)
    db.session.commit()

# ログ取得


def get_logs(user_id):
    return Log.query.filter_by(user_id=user_id).order_by(Log.timestamp.desc()).all()


@app.route('/')
def index():
    if current_user.is_authenticated:
        city = current_user.city or "Tokyo"
        weather, temp = get_weather(city, OPENWEATHER_API_KEY)

        CITY_NAME_MAP = {
            "Tokyo": "東京", "Osaka": "大阪", "Sapporo": "札幌", "Fukuoka": "福岡",
            "Nagoya": "名古屋", "Kanagawa": "神奈川", "Yokohama": "横浜", "Kyoto": "京都", "Kobe": "神戸"
        }
        city_ja = CITY_NAME_MAP.get(city, city)
        return render_template('index.html', weather=weather, temp=temp, city=city_ja)
    else:
        return redirect(url_for('register'))


def get_weather(city_name, api_key):
    # APIキーが設定されていない場合はNoneを返す
    if not api_key or api_key == "YOUR_OPENWEATHER_API_KEY":
        return None, None
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={api_key}&lang=ja&units=metric"
    try:
        res = requests.get(url)
        # HTTPステータスコードが200以外の場合も例外を発生させる
        res.raise_for_status()
        data = res.json()
        return data['weather'][0]['description'], data['main']['temp']
    except requests.exceptions.RequestException as e:
        print(f"OpenWeather APIとの通信エラー: {e}")
    except Exception as e:
        print(f"OpenWeather API処理中の予期せぬエラー: {e}")
    return None, None


@app.route('/ai', methods=['POST'])
@login_required
def ai():
    # フォームデータとJSONデータの両方に対応
    if request.is_json:
        req = request.get_json()
        mood = req.get('mood', '')
        mode = req.get('mode', 'normal')
    else:
        mood = request.form.get('mood', '')
        mode = request.form.get('mode', 'normal')

    mbti = current_user.mbti_type
    city = current_user.city or "Tokyo"
    weather, temp = get_weather(city, OPENWEATHER_API_KEY)

    mbti_text = f" ユーザーのMBTIタイプは {mbti} です。MBTIの性格傾向も考慮して、" if mbti and mbti.lower(
    ) != 'わからない' else ""
    weather_text = f" 現在の天気は「{weather}」、気温は{temp}℃です。天気や気温も考慮して、" if weather and temp else ""

    prompts = {
        'playlist': f"{mbti_text}{weather_text}今の気分は「{mood}」です。この気分にぴったりの日本の曲を10曲、1行ずつ「🎵 曲名 - 理由」の形式で出力してください。",
        'movie': f"{mbti_text}{weather_text}今の気分は「{mood}」です。この気分に合う名作の海外と日本の映画を5つ、1行ずつ「🎬 映画名 - 理由」の形式で出力してください。",
        'food': f"""{mbti_text}{weather_text}今の気分は「{mood}」です。この気分に合った食の選択肢を、料理・外食・コンビニ商品の中から5つ提案してください。それぞれ「🍽️ 食事名 - 理由 - 主な栄養素（例：たんぱく質、炭水化物、ビタミンC）」の形式で出力してください。料理が向かない気分のときは、外食やコンビニを優先して構いません。""",
        'normal': f"{mbti_text}{weather_text}今の気分は「{mood}」です。これに合う日本の曲を3つ、1行ずつ「🎵 曲名 - 理由」の形式で出力してください。次に、その気分にあう日本の映画を3つ、1行ずつ「🎬 映画名 - 理由」の形式で出力してください。最後に、今の気分にあう食事を3つ、1行ずつ「🍽️ 食事名 - 理由」の形式で出力してください。"
    }
    prompt = prompts.get(mode, prompts['normal'])

    GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL_NAME}:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    data = {"contents": [{"parts": [{"text": prompt}]}]}

    insert_log(current_user.id, mood, "user")

    try:
        response = requests.post(GEMINI_URL, headers=headers, json=data)
        response.raise_for_status()  # HTTPエラーがあれば例外を発生させる
        result = response.json()
        raw_text = result['candidates'][0]['content']['parts'][0]['text']
    except (requests.exceptions.RequestException, KeyError, IndexError) as e:
        print(f"Gemini APIとの通信エラーまたはデータ解析エラー: {e}")
        error_message = f"AIとの通信中にエラーが発生しました: {e}"
        insert_log(current_user.id, error_message, "assistant")
        return jsonify({'reply': error_message, 'movies': []}), 500
    except Exception as e:
        print(f"Gemini API処理中の予期せぬエラー: {e}")
        error_message = f"AI応答処理中に予期せぬエラーが発生しました: {e}"
        insert_log(current_user.id, error_message, "assistant")
        return jsonify({'reply': error_message, 'movies': []}), 500

    enriched_text = raw_text

    # YouTubeリンクの処理
    song_lines = re.findall(r'🎵 (.+?) -', raw_text)
    for song in song_lines:
        url = search_youtube_first_video(song)
        # re.escape()で特殊文字をエスケープして正規表現の誤作動を防ぐ
        enriched_text = re.sub(rf"(🎵\s*){re.escape(song)}(\s*-)",
                               rf"\1<a href='{url}' target='_blank' class='text-blue-400 underline'>{song}</a>\2", enriched_text, count=1)

    # 「近くのお店を探す」ボタンの追加 (アイコン付き、修正版)
    food_lines = re.findall(r'🍽️\s*(.+?)\s*-', enriched_text)
    for food in food_lines:
        food_id = re.sub(r'\s+', '_', food)
        button_html = f"""
        <button onclick="findNearbyRestaurants('{food}')" class='text-sm bg-white-600 hover:bg-white-700 text-white font-bold py-2 px-3 rounded-lg ml-2 shadow-md transform hover:-translate-y-px transition-all duration-300'>
            近くのお店を探す
        </button>
        <div id='restaurants_{food_id}' class='mt-2'></div>
        """
        enriched_text = re.sub(
            rf"(🍽️\s*{re.escape(food)}\s*-.*)", rf"\1 {button_html}", enriched_text, count=1)

    # 映画情報の処理
    def extract_movie_titles(text):
        pattern = r"🎬\s*(.+?)\s*-\s*.+"
        return re.findall(pattern, text)

    def search_movie_tmdb(title):
        # The Movie DBのAPIキー（必要ならこれも先頭に設定してください）
        url = "https://api.themoviedb.org/3/search/movie"
        params = {"api_key": TMDB_API_KEY, "query": title, "language": "ja-JP"}
        try:
            res = requests.get(url, params=params)
            res.raise_for_status()  # HTTPエラーがあれば例外を発生させる
            data = res.json()
            if data["results"]:
                movie = data["results"][0]
                return {
                    "title": movie.get("title"),
                    "overview": movie.get("overview"),
                    "release_date": movie.get("release_date"),
                    "poster_path": f"https://image.tmdb.org/t/p/w300{movie.get('poster_path')}" if movie.get("poster_path") else None,
                    "tmdb_url": f"https://www.themoviedb.org/movie/{movie.get('id')}"
                }
        except requests.exceptions.RequestException as e:
            print(f"TMDB APIとの通信エラー: {e}")
        except Exception as e:
            print(f"TMDB API処理中の予期せぬエラー: {e}")
        return None

    movie_titles = extract_movie_titles(raw_text)
    movie_infos = [info for title in movie_titles if (
        info := search_movie_tmdb(title))]

    insert_log(current_user.id, raw_text, "assistant")

    # movieモードかnormalモードの場合のみ映画情報を返す
    return jsonify({'reply': enriched_text, 'movies': movie_infos if mode in ['movie', 'normal'] else []})


@app.route('/find_restaurants')
@login_required
def find_restaurants():
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    food = request.args.get('food')

    if not all([lat, lon, food]):
        return jsonify({"error": "緯度、経度、食事が指定されていません。"}), 400

    # Google Maps Platform APIキーが設定されていない場合はエラーを返す
    if not GOOGLE_MAPS_API_KEY or GOOGLE_MAPS_API_KEY.strip() == "YOUR_GOOGLE_MAPS_API_KEY":
        return jsonify({"error": "Google Maps APIキーが設定されていません。adminにご連絡ください。"}), 500

    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": f"{lat},{lon}",
        "radius": 1500,  # 検索半径(メートル)
        "keyword": food,
        "language": "ja",
        "key": GOOGLE_MAPS_API_KEY.strip()  # APIキーの末尾の空白を除去
    }
    try:
        res = requests.get(url, params=params)
        res.raise_for_status()  # HTTPステータスコードが200以外の場合も例外を発生させる
        data = res.json()

        results = []
        for place in data.get("results", []):
            # GoogleマップのURLを構築。店名をURLエンコードする
            map_url = f"https://www.google.com/maps/search/?api=1&query={requests.utils.quote(place.get('name', ''))}&query_place_id={place.get('place_id', '')}"

            results.append({
                "name": place.get("name"),
                "vicinity": place.get("vicinity"),  # 住所
                "rating": place.get("rating", "N/A"),
                "url": map_url
            })
        return jsonify(results)
    except requests.exceptions.RequestException as e:
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("/find_restaurants でHTTPエラーが発生しました:")
        print(f"URL: {url}, Params: {params}")
        print(f"エラー内容: {e}")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        return jsonify({"error": f"レストラン検索APIとの通信に失敗しました。詳細: {e}"}), 500
    except Exception as e:
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("/find_restaurants で予期せぬエラーが発生しました:")
        print(f"エラー内容: {e}")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        return jsonify({"error": f"レストラン検索中に予期せぬエラーが発生しました。"}), 500


def search_youtube_first_video(query):
    # APIキーが設定されていない場合はデフォルトのURLを返す
    if not YOUTUBE_API_KEY or YOUTUBE_API_KEY == "YOUR_YOUTUBE_API_KEY":
        return "#"

    url = 'https://www.googleapis.com/youtube/v3/search'
    params = {
        'part': 'snippet',
        'q': f'{query} MV',
        'type': 'video',
        'maxResults': 5,
        'key': YOUTUBE_API_KEY,
        'regionCode': 'JP',
        'relevanceLanguage': 'ja',
        'order': 'relevance'
    }
    try:
        res = requests.get(url, params=params)
        res.raise_for_status()
        data = res.json()
        for item in data.get("items", []):
            if 'videoId' in item['id']:
                return f"https://www.youtube.com/watch?v={item['id']['videoId']}"
    except requests.exceptions.RequestException as e:
        print(f"YouTube検索エラー: {e}")
    except Exception as e:
        print(f"YouTube検索処理中の予期せぬエラー: {e}")
    return "#"


def search_movie_tmdb(title):
    # TMDB APIキーが設定されていない場合はNoneを返す
    if not TMDB_API_KEY:
        return None

    url = "https://api.themoviedb.org/3/search/movie"
    params = {
        "api_key": TMDB_API_KEY,
        "query": title,
        "language": "ja-JP"
    }
    try:
        res = requests.get(url, params=params)
        res.raise_for_status()
        data = res.json()
        if data["results"]:
            movie = data["results"][0]
            return {
                "title": movie.get("title"),
                "overview": movie.get("overview"),
                "release_date": movie.get("release_date"),
                "poster_path": f"https://image.tmdb.org/t/p/w300{movie.get('poster_path')}" if movie.get("poster_path") else None,
                "tmdb_url": f"https://www.themoviedb.org/movie/{movie.get('id')}"
            }
    except requests.exceptions.RequestException as e:
        print(f"TMDB検索エラー: {e}")
    except Exception as e:
        print(f"TMDB検索処理中の予期せぬエラー: {e}")
    return None


@app.route('/logs')
@login_required
def show_logs():
    selected_date = request.args.get('date')
    logs_query = Log.query.filter_by(user_id=current_user.id)
    if selected_date:
        try:
            date_obj = datetime.strptime(selected_date, '%Y-%m-%d').date()
            logs_query = logs_query.filter(
                db.func.date(Log.timestamp) == date_obj)
        except ValueError:
            flash("日付形式が不正です", "error")

    logs = logs_query.order_by(Log.timestamp.desc()).all()
    grouped_logs = defaultdict(list)
    for log in logs:
        grouped_logs[log.timestamp.strftime('%Y-%m-%d')].append(log)

    return render_template('logs.html', grouped_logs=dict(sorted(grouped_logs.items(), reverse=True)), selected_date=selected_date)


@app.route('/logs/delete/<int:log_id>', methods=['POST'])
@login_required
def delete_log(log_id):
    log = Log.query.get_or_404(log_id)
    if log.user_id != current_user.id:
        flash("削除権限がありません。")
        return redirect(url_for('show_logs'))
    db.session.delete(log)
    db.session.commit()
    flash("ログを削除しました。")
    return redirect(url_for('show_logs'))


@app.route('/mbti')
def mbti():
    return render_template('mbti.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        mbti_type = request.form['mbti_type']
        city = request.form['city']
        if User.query.filter_by(email=email).first():
            flash('このメールアドレスは既に登録されています。')
            return redirect(url_for('register'))
        new_user = User(username=username, email=email,
                        mbti_type=mbti_type, city=city)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash('登録成功！ログインしてください。')
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('メールアドレスまたはパスワードが間違っています。')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('ログアウトしました。')
    return redirect(url_for('login'))


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.username = request.form['username']
        current_user.mbti_type = request.form['mbti_type']
        current_user.city = request.form['city']
        db.session.commit()
        flash("プロフィールを更新しました！")
        return redirect(url_for('profile'))
    return render_template('profile.html')


if __name__ == '__main__':
    print("🌟 Flaskサーバー起動中… http://127.0.0.1:5000/")
    app.run(debug=True)
