"""
ChargeMind Demo 配置
"""
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_CLEANED = PROJECT_ROOT.parent / "data" / "cleaned"
CHROMA_PATH = PROJECT_ROOT / "chroma_db"

# Kimi API
KIMI_API_KEY = os.getenv("KIMI_API_KEY", "")
KIMI_BASE_URL = os.getenv("KIMI_BASE_URL", "https://api.kimi.com/coding/v1")

# 默认模型
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "kimi-latest")

# CORS（开发环境放行所有）
CORS_ORIGINS = ["*"]
