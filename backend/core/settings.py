import os

# 檢查基本資料
DEBUG = True
ALLOWED_HOSTS = ['*']

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')

if not SECRET_KEY:
    raise RuntimeError("無法讀取 DJANGO_SECRET_KEY，請檢查 entrypoint.sh")



INSTALLED_APPS = [
    'daphne',  # 必須放在第一個
    'django.contrib.admin',
    # ... 其他預設 app
    'channels',
    'corsheaders',
    'game',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware', # 放在最上面
    # ...
]

CORS_ALLOW_ALL_ORIGINS = True # 開發初期先全開
ASGI_APPLICATION = 'core.asgi.application'
REDIS_URL = os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/0')

# 這裡先用記憶體模擬 Redis，方便你沒開 Docker 也能跑，
# 但正式開發建議改用 redis://redis:6379
CHANNEL_LAYERS = {
    "default": {
        # "BACKEND": "channels.layers.InMemoryChannelLayer",
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [REDIS_URL],
        },
    },
}