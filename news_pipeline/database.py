"""SQLite 数据库操作"""

import sqlite3
from datetime import datetime
from typing import List, Optional
from .config import DATABASE_PATH


def get_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """初始化数据库表"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            link TEXT UNIQUE,
            pub_date DATETIME,
            source TEXT DEFAULT 'sina',
            category TEXT,
            is_processed BOOLEAN DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_pub_date ON news(pub_date)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_processed ON news(is_processed)
    """)

    conn.commit()
    conn.close()


def insert_news(title: str, link: str, pub_date: str, source: str = "sina") -> bool:
    """插入单条新闻，如果链接已存在则忽略"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT OR IGNORE INTO news (title, link, pub_date, source)
            VALUES (?, ?, ?, ?)
        """, (title, link, pub_date, source))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"插入新闻失败: {e}")
        return False
    finally:
        conn.close()


def insert_many_news(news_list: List[dict]) -> int:
    """批量插入新闻，返回插入数量"""
    conn = get_connection()
    cursor = conn.cursor()
    count = 0

    try:
        for news in news_list:
            cursor.execute("""
                INSERT OR IGNORE INTO news (title, link, pub_date, source)
                VALUES (?, ?, ?, ?)
            """, (news["title"], news["link"], news["pub_date"], news["source"]))
            if cursor.rowcount > 0:
                count += 1
        conn.commit()
    except Exception as e:
        print(f"批量插入失败: {e}")
    finally:
        conn.close()

    return count


def get_recent_news(limit: int = 50, trading_hour_start: int = 12) -> List[dict]:
    """获取最近的新闻（按时间倒序）"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, title, link, pub_date, source, category, is_processed
        FROM news
        WHERE DATE(pub_date) >= DATE('now', '-3 days')
        ORDER BY pub_date DESC
        LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_unprocessed_news(limit: int = 20) -> List[dict]:
    """获取未处理的新闻"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, title, link, pub_date, source
        FROM news
        WHERE is_processed = 0
        ORDER BY pub_date DESC
        LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def mark_as_processed(news_ids: List[int]) -> bool:
    """标记新闻为已处理"""
    if not news_ids:
        return False

    conn = get_connection()
    cursor = conn.cursor()

    try:
        placeholders = ",".join(["?"] * len(news_ids))
        cursor.execute(f"""
            UPDATE news
            SET is_processed = 1
            WHERE id IN ({placeholders})
        """, news_ids)
        conn.commit()
        return True
    except Exception as e:
        print(f"标记失败: {e}")
        return False
    finally:
        conn.close()


def get_news_by_ids(news_ids: List[int]) -> List[dict]:
    """根据ID列表获取新闻"""
    if not news_ids:
        return []

    conn = get_connection()
    cursor = conn.cursor()

    placeholders = ",".join(["?"] * len(news_ids))
    cursor.execute(f"""
        SELECT id, title, link, pub_date, source
        FROM news
        WHERE id IN ({placeholders})
        ORDER BY pub_date DESC
    """, news_ids)

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_all_news_count() -> int:
    """获取新闻总数"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM news")
    count = cursor.fetchone()[0]
    conn.close()
    return count


def clear_old_news(days: int = 7) -> int:
    """清理旧新闻（保留最近N天）"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM news
        WHERE DATE(created_at) < DATE('now', '-' || ? || ' days')
    """, (days,))

    count = cursor.rowcount
    conn.commit()
    conn.close()
    return count


if __name__ == "__main__":
    # 初始化数据库
    init_database()
    print(f"数据库初始化完成: {DATABASE_PATH}")
    print(f"新闻总数: {get_all_news_count()}")
