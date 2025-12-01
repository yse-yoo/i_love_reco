# Alembic の設定ファイルから logging 設定を読み込む
from logging.config import fileConfig

# SQLAlchemy から必要な関数をインポート
from sqlalchemy import engine_from_config
from sqlalchemy import pool

# Alembic の context オブジェクトをインポート（マイグレーションに必要な設定を保持）
from alembic import context

# Alembic の Config オブジェクトを取得（alembic.ini の値を参照できる）
config = context.config

# ログ設定（alembic.ini に設定があれば読み込む）
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ▼▼▼▼▼ ここにモデルのメタデータを追加 ▼▼▼▼▼
# autogenerate 機能を使うためには、ここに SQLAlchemy の metadata を指定する必要がある
# 例:
# from yourapp.models import Base
# target_metadata = Base.metadata

target_metadata = None  # 初期状態では None。使いたい場合は上で読み込んで代入。

# その他、alembic.ini に定義した独自の設定値を取得したい場合
# my_option = config.get_main_option("my_important_option")


# --- オフラインモード用マイグレーション処理 ---
def run_migrations_offline() -> None:
    """
    オフラインモードでマイグレーションを実行します。

    データベースへの接続は行わず、SQL文を標準出力に出力します。
    （DBがまだ存在しないときやスクリプトだけ作りたい場合など）
    """
    url = config.get_main_option("sqlalchemy.url")  # DB接続URLを取得
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,  # プレースホルダではなくリテラルで出力
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


# --- オンラインモード用マイグレーション処理 ---
def run_migrations_online() -> None:
    """
    オンラインモードでマイグレーションを実行します。

    実際にDBへ接続し、マイグレーションを適用します。
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",  # sqlalchemy.url などの接頭辞
        poolclass=pool.NullPool,  # 接続プールは使用しない（マイグレーションには不要）
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata  # 自動生成のためにモデルのメタデータを設定
        )

        with context.begin_transaction():
            context.run_migrations()


# 実行モードに応じて、オンライン・オフラインを切り替え
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
