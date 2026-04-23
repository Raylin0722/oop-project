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

# 這裡先用記憶體模擬 Redis，方便你沒開 Docker 也能跑，
# 但正式開發建議改用 redis://redis:6379
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    },
}