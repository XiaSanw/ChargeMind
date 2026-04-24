"""
ChargeMind Demo 配置
"""
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_CLEANED = PROJECT_ROOT.parent / "data" / "cleaned"
CHROMA_PATH = PROJECT_ROOT / "chroma_db"

# Kimi API（复用 kimi-cli 的环境变量或手动设置）
KIMI_API_KEY = os.getenv("KIMI_API_KEY", "")
KIMI_BASE_URL = os.getenv("KIMI_BASE_URL", "https://api.moonshot.cn/v1")

# 默认模型
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "kimi-latest")

# CORS（开发环境放行所有）
CORS_ORIGINS = ["*"]
