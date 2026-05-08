"""新闻 Pipeline 配置"""

import os

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 数据库
DATABASE_PATH = os.path.join(PROJECT_ROOT, "data", "news.db")

# MiniMax API
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_BASE_URL = os.environ.get("ANTHROPIC_BASE_URL", "https://api.minimaxi.com/anthropic")
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "MiniMax-M2.7")
ANTHROPIC_AUTH_TOKEN = os.environ.get("ANTHROPIC_AUTH_TOKEN", "")

# 新闻 RSS 源
RSS_SOURCES = [
    {
        "name": "sina_finance",
        "url": "https://rss.sina.com.cn/news/china/focus15.xml",
        "source": "新浪财经"
    },
    {
        "name": "sina_stock",
        "url": "https://rss.sina.com.cn/roll/index.d.html",
        "source": "新浪股票"
    }
]

# 时间过滤
TRADING_HOUR_START = 12  # 中午12点开始（获取午盘后的新闻）
TRADING_DAYS_BACK = 2    # 最多回溯2个交易日

# 视频输出
VIDEO_OUTPUT_DIR = os.path.join(PROJECT_ROOT, "audio")
SCENES_DIR = os.path.join(PROJECT_ROOT, "scenes")
AUDIO_DIR = os.path.join(PROJECT_ROOT, "audio")

# MOSS TTS
MOSS_CLONE_SCRIPT = os.path.join(PROJECT_ROOT, "moss_clone.sh")
