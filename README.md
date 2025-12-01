### venv
```bash
python3 -m venv venv
```

## Linux
```bash
source venv/bin/activate
```

## Windows
```bash
.\.venv\Scripts\activate
```

```bash
set FLASK_APP=app.py
```

## サーバ起動
### Flask
```bash
flask run --host=0.0.0.0 --reload
```

### gunicorn
```bash
gunicorn -D --workers 4 -b 0.0.0.0:8000 app:app
```

## その他必要なパッケージ
### gunicorn
```bash
pip install gunicorn
```

### Windows
```bash
pip install waitress
```

```bash
waitress-serve --listen=0.0.0.0:8000 app:app
```

# AWS EC2 作業
## yse グループ追加
```bash
sudo groupadd yse
```

### yse グループに ubuntu ユーザ追加
```bash
sudo usermod -aG yse ubuntu
```

### yse グループに www-data ユーザ追加
```bash
sudo usermod -aG yse www-data
```

## アクセス権変更
```bash
sudo chown -R www-data:yse /var/www/html
sudo find /var/www/html -type d -exec chmod 775 {} \;
sudo find /var/www/html -type f -exec chmod 664 {} \;
```

### 新規ファイルの作成権限
```bash
sudo chmod g+s /var/www/html
```

# Python
## パッケージリストの更新
```bash
sudo apt update
```

## Python 3 開発ツールと venv のインストール
```bash
sudo apt install python3-pip python3-venv
```

## プロジェクト作成
```bash
mkdir プロジェクト名
```

### venv
```bash
python3 -m venv .venv
```

### activate
```bash
source venv/bin/activate
```

### パッケージインストール
```bash
pip install -r requirements.txt
```

#### バックグランドサーバー（本番用）
```bash
pip install gunicorn
```

## アプリ起動
### Flask デフォルトの場合
```bash
flask run --host=0.0.0.0
```

### gunicorn の場合
#### 開発モード軌道
```bash
gunicorn --workers 3 -b 0.0.0.0:5000 app:app
```

#### バックグランド軌道
```bash
gunicorn -D --workers 3 -b 0.0.0.0:5000 app:app
```

#### 切断
```bash
ps aux | grep gunicorn
```

一番小さい、プロセスを kill
```bash
kill <PID>
```

## Nginx
### Nginx テスト
```bash
sudo nginx -t
```

### Nginx 再起動
```bash
sudo systemctl restart nginx
```