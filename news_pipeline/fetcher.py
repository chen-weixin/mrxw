"""新闻获取模块 - 从新浪财经和东方财富获取 RSS/API 新闻"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from .config import RSS_SOURCES
from .database import insert_many_news, init_database


class NewsFetcher:
    """新闻获取器"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        })

    def fetch_sina_rss(self, source: Dict) -> List[Dict]:
        """获取新浪财经 RSS"""
        news_list = []

        try:
            response = self.session.get(source["url"], timeout=10)
            response.encoding = "utf-8"

            soup = BeautifulSoup(response.text, "xml")

            # 解析 RSS
            items = soup.find_all("item")

            for item in items:
                try:
                    title = item.find("title")
                    link = item.find("link")
                    pub_date = item.find("pubDate")

                    if title and link:
                        title_text = title.get_text(strip=True)
                        link_text = link.get_text(strip=True)

                        # 解析发布时间
                        pub_date_text = ""
                        if pub_date:
                            pub_date_text = pub_date.get_text(strip=True)
                            pub_date_text = self._parse_date(pub_date_text)

                        news_list.append({
                            "title": title_text,
                            "link": link_text,
                            "pub_date": pub_date_text,
                            "source": source["source"]
                        })
                except Exception as e:
                    print(f"解析新浪条目失败: {e}")
                    continue

        except Exception as e:
            print(f"获取新浪 RSS 失败: {source['url']} - {e}")

        return news_list

    def fetch_eastmoney_24h(self) -> List[Dict]:
        """获取东方财富 24 小时滚动新闻"""
        news_list = []

        # 东方财富滚动新闻 API
        api_url = "https://feed.eastmoney.com/moreCateList.html"

        try:
            # 尝试获取滚动新闻
            response = self.session.get(api_url, timeout=10)
            response.encoding = "utf-8"
            soup = BeautifulSoup(response.text, "html.parser")

            # 查找新闻条目
            items = soup.select(".news-list-item, .article-item, .list-item")

            for item in items[:30]:  # 限制数量
                try:
                    title_elem = item.select_one("a, .title, .news-title")
                    time_elem = item.select_one("span.time, .date, .news-time")

                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        link = title_elem.get("href", "")

                        # 补充完整链接
                        if link and not link.startswith("http"):
                            link = "https://finance.eastmoney.com" + link

                        pub_date = ""
                        if time_elem:
                            pub_date = time_elem.get_text(strip=True)
                            pub_date = self._parse_date(pub_date)
                        else:
                            pub_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                        news_list.append({
                            "title": title,
                            "link": link,
                            "pub_date": pub_date,
                            "source": "东方财富"
                        })
                except Exception as e:
                    continue

        except Exception as e:
            print(f"获取东方财富新闻失败: {e}")

        # 如果东方财富网页抓取失败，尝试 API 方式
        if not news_list:
            news_list = self._fetch_eastmoney_api()

        return news_list

    def _fetch_eastmoney_api(self) -> List[Dict]:
        """东方财富 API 方式获取"""
        news_list = []

        api_url = "https://np-listapi.eastmoney.com"
        params = {
            "client": "web",
            "type": "24h",
            "page": 1,
            "pageSize": 30
        }

        try:
            response = self.session.get(api_url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("data"):
                    for item in data["data"]:
                        news_list.append({
                            "title": item.get("title", ""),
                            "link": item.get("url", ""),
                            "pub_date": item.get("showtime", ""),
                            "source": "东方财富"
                        })
        except Exception as e:
            print(f"东方财富 API 请求失败: {e}")

        return news_list

    def _parse_date(self, date_str: str) -> str:
        """解析日期字符串"""
        if not date_str:
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 尝试多种日期格式
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%a, %d %b %Y %H:%M:%S",
            "%Y年%m月%d日 %H:%M",
            "%m/%d/%Y %H:%M:%S",
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(date_str.strip(), fmt)
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                continue

        # 如果都解析失败，返回当前时间
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def is_trading_time(self, pub_date: datetime) -> bool:
        """判断是否在交易时间段（中午12点之后）"""
        # 只获取中午12点之后的新闻
        return pub_date.hour >= 12

    def is_trading_day(self, date: datetime) -> bool:
        """判断是否是交易日（排除周末）"""
        # 0=周一, 6=周日
        return date.weekday() < 5

    def filter_trading_news(self, news_list: List[Dict]) -> List[Dict]:
        """过滤出交易时间段的新闻"""
        filtered = []

        for news in news_list:
            try:
                pub_date = datetime.strptime(news["pub_date"], "%Y-%m-%d %H:%M:%S")
                if self.is_trading_day(pub_date):
                    filtered.append(news)
            except:
                # 解析失败也保留
                filtered.append(news)

        return filtered

    def fetch_all(self) -> List[Dict]:
        """获取所有来源的新闻"""
        all_news = []

        # 新浪财经
        print("正在获取新浪财经新闻...")
        for source in RSS_SOURCES:
            news = self.fetch_sina_rss(source)
            all_news.extend(news)
            print(f"  - {source['name']}: {len(news)} 条")

        # 东方财富
        print("正在获取东方财富新闻...")
        eastmoney_news = self.fetch_eastmoney_24h()
        all_news.extend(eastmoney_news)
        print(f"  - 东方财富: {len(eastmoney_news)} 条")

        # 去重（按标题）
        seen = set()
        unique_news = []
        for news in all_news:
            if news["title"] not in seen:
                seen.add(news["title"])
                unique_news.append(news)

        # 按时间排序
        unique_news.sort(key=lambda x: x["pub_date"], reverse=True)

        print(f"去重后共 {len(unique_news)} 条新闻")
        return unique_news


def fetch_and_save() -> int:
    """获取新闻并保存到数据库"""
    # 初始化数据库
    init_database()

    # 获取新闻
    fetcher = NewsFetcher()
    news_list = fetcher.fetch_all()

    if not news_list:
        print("没有获取到新闻")
        return 0

    # 保存到数据库
    count = insert_many_news(news_list)
    print(f"已保存 {count} 条新新闻到数据库")
    return count


if __name__ == "__main__":
    fetch_and_save()
