"""新闻获取模块 - 东方财富 7*24 滚动新闻 API"""

import requests
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from .database import insert_many_news, init_database


class NewsFetcher:
    """新闻获取器 - 东方财富 7*24 滚动新闻"""

    # API 配置
    API_URL = "https://np-listapi.eastmoney.com/comm/web/getFastNewsList"

    # 新闻分类
    COLUMNS = {
        "102": "7*24全球直播",    # 主要使用这个
        "yw": "焦点新闻",
        "zhiboall": "股市直播",
        "jjsj": "经济数据",
        "qqgs": "全球股市",
        "wh": "外汇",
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })

    def fetch_page(self, fast_column: str = "102", page_size: int = 30, sort_end: str = "0") -> Dict:
        """
        获取单页新闻

        Args:
            fast_column: 新闻分类代码
            page_size: 每页数量
            sort_end: 分页标识，首次 "0"，后续使用上一次的 realSort

        Returns:
            API 响应数据
        """
        params = {
            "client": "web",
            "biz": "web_724",
            "fastColumn": fast_column,
            "pageSize": page_size,
            "sortEnd": sort_end,
            "req_trace": str(uuid.uuid4())
        }

        try:
            response = self.session.get(self.API_URL, params=params, timeout=15)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"请求失败: {e}")

        return {}

    def fetch_scroll(self, fast_column: str = "102", max_pages: int = 5, max_news: int = 100) -> List[Dict]:
        """
        滚动获取多页新闻

        Args:
            fast_column: 新闻分类
            max_pages: 最大页数
            max_news: 最大新闻数

        Returns:
            新闻列表
        """
        news_list = []
        sort_end = "0"

        print(f"正在获取【{self.COLUMNS.get(fast_column, fast_column)}】滚动新闻...")

        for page in range(max_pages):
            if len(news_list) >= max_news:
                break

            data = self.fetch_page(fast_column, page_size=30, sort_end=sort_end)

            if data.get("code") != "1":
                print(f"  API 返回错误: {data.get('message', 'unknown')}")
                break

            news_data = data.get("data") or {}
            fast_news_list = news_data.get("fastNewsList") or []

            if not fast_news_list:
                print(f"  第 {page + 1} 页无数据，停止")
                break

            for item in fast_news_list:
                if len(news_list) >= max_news:
                    break

                news_list.append({
                    "title": item.get("title", ""),
                    "link": f"https://finance.eastmoney.com/kuaixun/{item.get('code', '')}.html",
                    "pub_date": item.get("showTime", ""),
                    "source": "东方财富",
                    "summary": item.get("summary", ""),
                    "stocks": ",".join(item.get("stockList", []) or [])
                })

            # 更新分页标识
            sort_end = news_data.get("sortEnd", "0")
            total = news_data.get("total", 0)
            print(f"  第 {page + 1} 页: 获取 {len(fast_news_list)} 条, 累计 {len(news_list)}/{total}")

        return news_list

    def fetch_all_sources(self, max_per_source: int = 50) -> List[Dict]:
        """
        获取多个分类的新闻

        Args:
            max_per_source: 每个来源的最大数量

        Returns:
            合并后的新闻列表
        """
        all_news = []

        # 主要获取 7*24 全球直播
        main_news = self.fetch_scroll("102", max_pages=5, max_news=max_per_source)
        all_news.extend(main_news)

        # 补充焦点新闻
        focus_news = self.fetch_scroll("yw", max_pages=2, max_news=30)
        all_news.extend(focus_news)

        # 去重（按标题）
        seen = set()
        unique_news = []
        for news in all_news:
            if news["title"] not in seen and news["title"]:
                seen.add(news["title"])
                unique_news.append(news)

        # 按时间排序
        unique_news.sort(key=lambda x: x["pub_date"], reverse=True)

        print(f"\n共获取 {len(unique_news)} 条去重后的新闻")
        return unique_news

    def fetch_today_only(self, max_news: int = 80) -> List[Dict]:
        """
        只获取今天的新闻（交易日中午12点之后）

        Args:
            max_news: 最大新闻数

        Returns:
            今天且交易时间段的新闻列表
        """
        today = datetime.now().strftime("%Y-%m-%d")
        news_list = self.fetch_scroll("102", max_pages=5, max_news=max_news * 2)

        # 过滤今天的新闻
        today_news = []
        for news in news_list:
            pub_date = news.get("pub_date", "")
            if pub_date.startswith(today):
                today_news.append(news)
            if len(today_news) >= max_news:
                break

        # 按时间倒序
        today_news.sort(key=lambda x: x["pub_date"], reverse=True)

        print(f"今天 ({today}) 新闻: {len(today_news)} 条")
        return today_news

    def _parse_date(self, date_str: str) -> str:
        """解析日期字符串"""
        if not date_str:
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(date_str.strip(), fmt)
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                continue

        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def fetch_and_save() -> int:
    """获取新闻并保存到数据库"""
    init_database()

    fetcher = NewsFetcher()
    news_list = fetcher.fetch_all_sources(max_per_source=60)

    if not news_list:
        print("没有获取到新闻")
        return 0

    count = insert_many_news(news_list)
    print(f"已保存 {count} 条新新闻到数据库")
    return count


def fetch_today_news() -> List[Dict]:
    """获取今天（交易日）的新闻"""
    init_database()

    fetcher = NewsFetcher()
    news_list = fetcher.fetch_today_only(max_news=80)

    # 保存到数据库
    if news_list:
        insert_many_news(news_list)
        print(f"已保存 {len(news_list)} 条今天新闻到数据库")

    return news_list


if __name__ == "__main__":
    fetch_and_save()
