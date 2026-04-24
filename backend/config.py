"""
ChargeMind Demo 配置
"""
import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent
ENV_PATH = PROJECT_ROOT.parent / ".env"
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)

DATA_CLEANED = PROJECT_ROOT.parent / "data" / "cleaned"
CHROMA_PATH = PROJECT_ROOT / "chroma_db"

# Kimi API — 仅用于 Embedding
KIMI_API_KEY = os.getenv("KIMI_API_KEY", "")
KIMI_BASE_URL = os.getenv("KIMI_BASE_URL", "https://api.kimi.com/coding/v1")

# DeepSeek API — 用于 Chat Completion
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

# 默认模型
CHAT_MODEL = os.getenv("CHAT_MODEL", "deepseek-v4-pro")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "moonshot-v1-embedding")

# CORS（开发环境放行所有）
CORS_ORIGINS = ["*"]
