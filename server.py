import os
import json
import re
from datetime import datetime, timedelta
from collections import defaultdict

import requests
from dotenv import load_dotenv

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

from werkzeug.security import generate_password_hash, check_password_hash

from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt
)

from flask_cors import CORS

# ================================
# 環境変数
# ================================
load_dotenv()

GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
TMDB_API_KEY = os.getenv("TMDB_API_KEY", "")

# ================================
# Flask アプリ & 設定
# ================================
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "your_secret_key")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///app.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# JWT
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "your_jwt_secret")
# アクセストークンの有効期限（必要に応じて調整）
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=12)

# CORS（フロントが別オリジンの場合）
CORS(app, resources={r"/api/*": {"origins": "*"}})

db = SQLAlchemy(app)
jwt = JWTManager(app)

# ================================
# モデル定義
# ================================
class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(150), nullable=False)
    mbti_type = db.Column(db.String(4), nullable=True)
    city = db.Column(db.String(50), nullable=True)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class Log(db.Model):
    __tablename__ = "logs"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    message = db.Column(db.Text, nullable=False)
    role = db.Column(db.String(20), nullable=False)  # "user" or "assistant"
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship("User", backref="logs")


# 初期化
with app.app_context():
    db.create_all()

# ================================
# ユーティリティ
# ================================
def insert_log(user_id: int, message: str, role: str):
    log = Log(user_id=user_id, message=message, role=role)
    db.session.add(log)
    db.session.commit()

def get_logs(user_id: int):
    return Log.query.filter_by(user_id=user_id).order_by(Log.timestamp.desc()).all()

def get_weather(city_name: str, api_key: str):
    """OpenWeather（現在）: 日本語 + 摂氏"""
    if not api_key or api_key == "YOUR_OPENWEATHER_API_KEY":
        return None, None
    url = "http://api.openweathermap.org/data/2.5/weather"
    params = {"q": city_name, "appid": api_key, "lang": "ja", "units": "metric"}
    try:
        res = requests.get(url, params=params, timeout=15)
        res.raise_for_status()
        data = res.json()
        return data["weather"][0]["description"], data["main"]["temp"]
    except requests.exceptions.RequestException as e:
        print(f"[OpenWeather] HTTPエラー: {e}")
    except Exception as e:
        print(f"[OpenWeather] 予期せぬエラー: {e}")
    return None, None

def search_youtube_first_video(query: str):
    """YouTubeで最初の動画URLを返す。APIキー未設定なら '#'. """
    if not YOUTUBE_API_KEY or YOUTUBE_API_KEY == "YOUR_YOUTUBE_API_KEY":
        return "#"
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": f"{query} MV",
        "type": "video",
        "maxResults": 5,
        "key": YOUTUBE_API_KEY,
        "regionCode": "JP",
        "relevanceLanguage": "ja",
        "order": "relevance",
    }
    try:
        res = requests.get(url, params=params, timeout=15)
        res.raise_for_status()
        data = res.json()
        for item in data.get("items", []):
            vid = item.get("id", {}).get("videoId")
            if vid:
                return f"https://www.youtube.com/watch?v={vid}"
    except requests.exceptions.RequestException as e:
        print(f"[YouTube] HTTPエラー: {e}")
    except Exception as e:
        print(f"[YouTube] 予期せぬエラー: {e}")
    return "#"

def search_movie_tmdb(title: str):
    """TMDB検索：最初の結果を返す（日本語）。未設定なら None。"""
    if not TMDB_API_KEY:
        return None
    url = "https://api.themoviedb.org/3/search/movie"
    params = {"api_key": TMDB_API_KEY, "query": title, "language": "ja-JP"}
    try:
        res = requests.get(url, params=params, timeout=15)
        res.raise_for_status()
        data = res.json()
        if data.get("results"):
            movie = data["results"][0]
            return {
                "title": movie.get("title"),
                "overview": movie.get("overview"),
                "release_date": movie.get("release_date"),
                "poster_path": f"https://image.tmdb.org/t/p/w300{movie.get('poster_path')}"
                if movie.get("poster_path")
                else None,
                "tmdb_url": f"https://www.themoviedb.org/movie/{movie.get('id')}",
            }
    except requests.exceptions.RequestException as e:
        print(f"[TMDB] HTTPエラー: {e}")
    except Exception as e:
        print(f"[TMDB] 予期せぬエラー: {e}")
    return None

# ================================
# API エンドポイント
# ================================
@app.route("/api/", methods=["GET"])
def index():
    return jsonify({"message": "Welcome to the I❤️RECO API"})

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "time": datetime.utcnow().isoformat()})

# --------------- 認証 ---------------
@app.route("/api/register", methods=["POST"])
def api_register():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    mbti_type = data.get("mbti_type")
    city = data.get("city")

    if not username or not email or not password:
        return jsonify({"error": "username, email, password は必須です"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "このメールアドレスは既に登録されています"}), 409

    user = User(username=username, email=email, mbti_type=mbti_type, city=city)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "registered ok", "user": {
        "id": user.id, "username": user.username, "email": user.email,
        "mbti_type": user.mbti_type, "city": user.city
    }}), 201

# ログイン
@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "メールアドレスまたはパスワードが間違っています"}), 401

    token = create_access_token(
        identity=str(user.id),
        additional_claims={
            "email": user.email,
            "city": user.city or "Tokyo",
            "mbti_type": user.mbti_type,
            "username": user.username,
        }
    )

    return jsonify({
        "token": token,
        "user": {
            "id": user.id,
            "email": user.email,
            "city": user.city,
            "mbti_type": user.mbti_type,
            "username": user.username,
        }
    })

# --------------- プロフィール ---------------
@app.route("/api/me", methods=["GET"])
@jwt_required()
def api_me():
    uid = int(get_jwt_identity())   # subとして取り出す
    claims = get_jwt()              # 追加claims全部とれる

    return jsonify({
        "id": uid,
        "email": claims.get("email"),
        "city": claims.get("city"),
        "mbti_type": claims.get("mbti_type"),
        "username": claims.get("username"),
    })

@app.route("/api/profile", methods=["GET", "PUT"])
@jwt_required()
def api_profile():
    identity = get_jwt_identity()
    u = User.query.get(identity["id"])
    if not u:
        return jsonify({"error": "user not found"}), 404

    if request.method == "PUT":
        data = request.get_json(silent=True) or {}
        u.username = data.get("username", u.username)
        u.mbti_type = data.get("mbti_type", u.mbti_type)
        u.city = data.get("city", u.city)
        db.session.commit()
        return jsonify({"message": "updated", "profile": {
            "username": u.username, "email": u.email,
            "mbti_type": u.mbti_type, "city": u.city
        }})

    return jsonify({
        "username": u.username,
        "email": u.email,
        "mbti_type": u.mbti_type,
        "city": u.city
    })

# --------------- 天気（ホーム用データ） ---------------
@app.route("/api/home", methods=["GET"])
@jwt_required()
def api_home():
    identity = get_jwt_identity()
    city = identity.get("city") or "Tokyo"
    weather, temp = get_weather(city, OPENWEATHER_API_KEY)
    return jsonify({"city": city, "weather": weather, "temp": temp})

# --------------- AI 推薦 ---------------
@app.route("/api/ai", methods=["POST"])
@jwt_required()
def api_ai():
    # identity (sub) はstringとなったので int化しつつ取得
    user_id = int(get_jwt_identity())

    payload = request.get_json(silent=True) or {}
    mood = payload.get("mood", "")
    mode = payload.get("mode", "normal")

    # ✅ テストモード
    if payload.get("test") is True:
        test_file_path = os.path.join("test_data", "ai_result.json")
        try:
            with open(test_file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # ログ記録
            insert_log(user_id, f"[TEST] {mood}", "user")
            return jsonify(data)
        except Exception as e:
            return jsonify({"error": f"テストデータの読み込みに失敗しました: {e}"}), 500

    # その他の属性は get_jwt() で claims として取得
    claims = get_jwt()
    mbti = claims.get("mbti_type")
    city = claims.get("city") or "Tokyo"


    weather, temp = get_weather(city, OPENWEATHER_API_KEY)

    mbti_text = (
        f" ユーザーのMBTIタイプは {mbti} です。MBTIの性格傾向も考慮して、"
        if mbti and mbti.lower() != "わからない"
        else ""
    )
    weather_text = (
        f" 現在の天気は「{weather}」、気温は{temp}℃です。天気や気温も考慮して、"
        if weather and temp is not None
        else ""
    )

    prompts = {
        "playlist": f"{mbti_text}{weather_text}今の気分は「{mood}」です。この気分にぴったりの日本の曲を10曲、1行ずつ「🎵 曲名 - 理由」の形式で出力してください。",
        "movie": f"{mbti_text}{weather_text}今の気分は「{mood}」です。この気分に合う名作の海外と日本の映画を5つ、1行ずつ「🎬 映画名 - 理由」の形式で出力してください。",
        "food": (
            f"{mbti_text}{weather_text}今の気分は「{mood}」です。この気分に合った食の選択肢を、"
            "料理・外食・コンビニ商品の中から5つ提案してください。それぞれ「🍽️ 食事名 - 理由 - 主な栄養素（例：たんぱく質、炭水化物、ビタミンC）」の形式で出力してください。"
            "料理が向かない気分のときは、外食やコンビニを優先して構いません。"
        ),
        "normal": (
            f"{mbti_text}{weather_text}今の気分は「{mood}」です。これに合う日本の曲を3つ、1行ずつ「🎵 曲名 - 理由」の形式で出力してください。"
            "次に、その気分にあう日本の映画を3つ、1行ずつ「🎬 映画名 - 理由」の形式で出力してください。"
            "最後に、今の気分にあう食事を3つ、1行ずつ「🍽️ 食事名 - 理由」の形式で出力してください。"
        ),
    }
    prompt = prompts.get(mode, prompts["normal"])

    # ログ記録（入力）
    insert_log(user_id, mood, "user")

    # --- Gemini 呼び出し ---
    raw_text = ""
    if not GEMINI_MODEL_NAME or not GEMINI_API_KEY:
        raw_text = "（開発モード）APIキー未設定のためダミー応答：\n🎵 Pretender - 前向きになれる\n🎬 君の名は。 - 切なくも温かい\n🍽️ 親子丼 - たんぱく質・炭水化物"
    else:
        GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL_NAME}:generateContent?key={GEMINI_API_KEY}"
        headers = {"Content-Type": "application/json"}
        data = {"contents": [{"parts": [{"text": prompt}]}]}

        try:
            response = requests.post(GEMINI_URL, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            raw_text = result["candidates"][0]["content"]["parts"][0]["text"]
        except (requests.exceptions.RequestException, KeyError, IndexError) as e:
            err = f"AI通信エラー: {e}"
            insert_log(user_id, err, "assistant")
            return jsonify({"error": err, "reply": "", "movies": []}), 502
        except Exception as e:
            err = f"AI応答処理中の予期せぬエラー: {e}"
            insert_log(user_id, err, "assistant")
            return jsonify({"error": err, "reply": "", "movies": []}), 500

    # --- YouTubeリンク埋め込み ---
    enriched_text = raw_text
    song_lines = re.findall(r"🎵\s*(.+?)\s*-", raw_text)
    for song in song_lines:
        url = search_youtube_first_video(song)
        enriched_text = re.sub(
            rf"(🎵\s*){re.escape(song)}(\s*-)","\\1<a href='"+url+"' target='_blank' rel='noopener'>"+song+"</a>\\2",
            enriched_text,
            count=1,
        )

    # --- 食事抽出 ---
    food_titles = re.findall(r"🍽️\s*(.+?)\s*-", enriched_text)

    # --- 映画 ---
    def extract_movie_titles(text: str):
        return re.findall(r"🎬\s*(.+?)\s*-\s*.+", text)

    movie_titles = extract_movie_titles(raw_text)
    movie_infos = [info for title in movie_titles if (info := search_movie_tmdb(title))]

    # ログ記録（AI生テキスト）
    insert_log(user_id, raw_text, "assistant")

    return jsonify({
        "reply": enriched_text,
        "songs": [{"title": s, "youtube": search_youtube_first_video(s)} for s in song_lines],
        "foods": [{"name": f} for f in food_titles],
        "movies": movie_infos if mode in ["movie", "normal"] else [],
    })

# --------------- レストラン検索 ---------------

@app.route("/api/find_restaurants", methods=["GET"])
@jwt_required()
def api_find_restaurants():
    lat = request.args.get("lat")
    lon = request.args.get("lon")
    food = request.args.get("food")

    if not all([lat, lon, food]):
        return jsonify({"error": "lat, lon, food は必須です"}), 400

    if not GOOGLE_MAPS_API_KEY or GOOGLE_MAPS_API_KEY.strip() == "YOUR_GOOGLE_MAPS_API_KEY":
        return jsonify({"error": "Google Maps APIキーが設定されていません"}), 500

    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": f"{lat},{lon}",
        "radius": 1500,
        "keyword": food,
        "language": "ja",
        "key": GOOGLE_MAPS_API_KEY.strip(),
    }
    try:
        res = requests.get(url, params=params, timeout=20)
        res.raise_for_status()
        data = res.json()

        results = []
        for place in data.get("results", []):
            map_url = (
                "https://www.google.com/maps/search/?api=1&query="
                f"{requests.utils.quote(place.get('name', ''))}"
                f"&query_place_id={place.get('place_id', '')}"
            )
            results.append({
                "name": place.get("name"),
                "vicinity": place.get("vicinity"),
                "rating": place.get("rating", "N/A"),
                "place_id": place.get("place_id"),
                "url": map_url
            })
        return jsonify({"restaurants": results})
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"レストラン検索APIエラー: {e}"}), 502
    except Exception as e:
        return jsonify({"error": f"レストラン検索中の予期せぬエラー: {e}"}), 500

# --------------- ログ ---------------

@app.route("/api/logs", methods=["GET"])
@jwt_required()
def api_logs():
    identity = get_jwt_identity()
    user_id = identity["id"]

    # ?date=YYYY-MM-DD を指定するとその日のみ
    selected_date = request.args.get("date")
    q = Log.query.filter_by(user_id=user_id)
    if selected_date:
        try:
            date_obj = datetime.strptime(selected_date, "%Y-%m-%d").date()
            q = q.filter(db.func.date(Log.timestamp) == date_obj)
        except ValueError:
            return jsonify({"error": "date は YYYY-MM-DD 形式で指定してください"}), 400

    logs = q.order_by(Log.timestamp.desc()).all()
    return jsonify([
        {
            "id": l.id,
            "message": l.message,
            "role": l.role,
            "timestamp": l.timestamp.isoformat()
        } for l in logs
    ])

@app.route("/api/logs/<int:log_id>", methods=["DELETE"])
@jwt_required()
def api_delete_log(log_id: int):
    identity = get_jwt_identity()
    user_id = identity["id"]

    log = Log.query.get_or_404(log_id)
    if log.user_id != user_id:
        return jsonify({"error": "権限がありません"}), 403

    db.session.delete(log)
    db.session.commit()
    return jsonify({"message": "deleted"})

# ================================
# エラーハンドラ（JSON専用）
# ================================
@app.errorhandler(404)
def not_found(_):
    return jsonify({"error": "Not Found"}), 404

@app.errorhandler(405)
def method_not_allowed(_):
    return jsonify({"error": "Method Not Allowed"}), 405

@app.errorhandler(500)
def internal_error(e):
    return jsonify({"error": f"Internal Server Error: {e}"}), 500

# ================================
# エントリポイント
# ================================
if __name__ == "__main__":
    print("🌟 Flask JSON API サーバー起動中… http://0.0.0.0:5000/(Android: http://10.0.2.2:5000/)")
    app.run(host="0.0.0.0", port=5000, debug=True)