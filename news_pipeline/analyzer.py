"""LLM 分析模块 - 调用 MiniMax API 进行新闻分析"""

import os
import json
import re
import requests
from typing import List, Dict, Optional
from .config import ANTHROPIC_API_KEY, ANTHROPIC_BASE_URL, ANTHROPIC_MODEL, ANTHROPIC_AUTH_TOKEN
from .database import get_recent_news, get_news_by_ids


class NewsAnalyzer:
    """新闻分析器"""

    def __init__(self):
        self.api_key = ANTHROPIC_API_KEY
        self.base_url = ANTHROPIC_BASE_URL
        self.model = ANTHROPIC_MODEL
        self.auth_token = ANTHROPIC_AUTH_TOKEN

    def _call_api(self, prompt: str, max_tokens: int = 4096) -> str:
        """调用 MiniMax API"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.auth_token}"
        }

        data = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

        try:
            response = requests.post(
                f"{self.base_url}/v1/messages",
                headers=headers,
                json=data,
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                # MiniMax 返回格式：content 是数组，可能包含 thinking 和 text
                content_list = result.get("content", [])
                for item in content_list:
                    if item.get("type") == "text":
                        return item.get("text", "")
                # 如果没有 text 类型，返回第一个内容
                if content_list:
                    return content_list[0].get("text", "")
                return ""
            else:
                return f"API 调用失败: {response.status_code} - {response.text}"

        except Exception as e:
            return f"请求异常: {e}"

    def filter_news(self, news_list: List[Dict]) -> str:
        """
        调用 LLM 进行新闻初筛
        返回 LLM 的候选列表输出
        """
        if not news_list:
            return "没有新闻可供分析"

        # 构建新闻列表文本
        news_text = "\n".join([
            f"{i+1}. {news['title']} ({news.get('pub_date', '未知时间')})"
            for i, news in enumerate(news_list)
        ])

        prompt = f"""你是一个财经因果逻辑裁判官。

任务：从以下新闻列表中，筛选出**真正能驱动未来产业变化**的硬核事件。

【筛选规则 - 负面清单】必须删除：
1. 行情回顾（"今日XX板块大涨"、"资金净流入XX亿"、"XX股涨停"）
2. 机构观点（"分析师认为"、"XX证券研报称"、"维持买入评级"）
3. 无效废话（否认的传闻、无实质内容的会议提醒）

【筛选规则 - 正面清单】只保留这4类：
1. 行政命令/法规（已发布，对未来产生约束的文件、通知）
2. 价格变更/供需异动（调价函、库存极值、停产检修通知）
3. 日历事件（已定档的发布会、解禁日、产品上线日）
4. 技术/产品突破（已获批文、已发布新品）

请按以下格式输出候选新闻：

## 候选新闻列表

1. [标题]
   - 类型：[行政/价格/日历/技术]
   - 摘要：[一句话描述核心事实]
   - 逻辑传导：[可能影响的行业]

...

【待筛选新闻】
{news_text}

## 选择指令
请回复 **选择的编号**（如：1, 3, 5），我会为你深度分析。
只选择最重要的3-5条，不要超过5条。
"""

        try:
            return self._call_api(prompt, max_tokens=4096)

        except Exception as e:
            print(f"LLM 调用失败: {e}")
            return f"分析失败: {e}"

    def parse_user_selection(self, llm_output: str, max_news: int) -> List[int]:
        """
        解析用户选择
        从 LLM 输出中提取编号，或等待用户输入
        """
        # 尝试从 LLM 输出中提取编号
        numbers = re.findall(r'\d+', llm_output)

        # 如果 LLM 已经给了选择
        if numbers:
            # 取最后一组数字作为选择
            for num_str in reversed(numbers):
                num = int(num_str)
                if 1 <= num <= max_news:
                    # 尝试解析范围格式如 "1, 3, 5" 或 "1-3"
                    selections = []
                    remaining = llm_output
                    while remaining:
                        match = re.search(r'(\d+)', remaining)
                        if match:
                            n = int(match.group(1))
                            if 1 <= n <= max_news and n not in selections:
                                selections.append(n)
                            remaining = remaining[match.end():]
                        else:
                            break
                    if selections:
                        return sorted(selections)

        return []

    def analyze_selected_news(self, selected_ids: List[int]) -> Dict:
        """
        对用户选择的新闻进行深度因果分析
        """
        # 获取新闻详情
        news_list = get_news_by_ids(selected_ids)

        if not news_list:
            return {"error": "没有找到对应的新闻"}

        # 构建新闻内容
        news_content = "\n\n".join([
            f"【新闻 {i+1}】\n标题: {news['title']}\n时间: {news.get('pub_date', '未知')}"
            for i, news in enumerate(news_list)
        ])

        prompt = f"""你是一个专业的财经分析师。

针对用户选择的以下新闻，请进行深度因果分析：

{news_content}

【分析要求】
对每条新闻，输出以下结构：

## 新闻 [N]: [标题]

### 核心事实
[客观陈述：发生了什么]

### 因果逻辑传导
**直接影响：** [对什么产生直接影响]

**传导路径：**
[具体传导路径]

**深层逻辑：**
[背后的深层原因或趋势]

### 受影响行业
| 行业 | 影响方向 | 影响程度 |
|------|----------|----------|
| 行业A | 利好/利空 | 高/中/低 |

### 受益/受损企业
**利好企业：** [企业简称列表]
**利空企业：** [企业简称列表]

### 视频脚本素材
**开场白：** [一句话引入]
**核心观点：** [1-2句话]
**总结：** [对投资者的提醒]

---

请用 JSON 格式输出所有分析结果，格式如下：
{{
  "news_list": [
    {{
      "title": "标题",
      "core_fact": "核心事实",
      "causality": {{
        "direct_impact": "直接影响",
        "transmission_path": "传导路径",
        "deep_logic": "深层逻辑"
      }},
      "industries": [
        {{"name": "行业A", "direction": "利好", "degree": "高"}}
      ],
      "companies": {{
        "benefited": ["企业A", "企业B"],
        "harmed": ["企业C"]
      }},
      "video_material": {{
        "intro": "开场白",
        "core_point": "核心观点",
        "summary": "总结"
      }}
    }}
  ]
}}

请确保输出有效的 JSON 格式。
"""

        try:
            result_text = self._call_api(prompt, max_tokens=8192)

            if result_text.startswith("API 调用失败") or result_text.startswith("请求异常"):
                return {"error": result_text}

            # 尝试提取 JSON
            json_match = re.search(r'\{[\s\S]*\}', result_text)
            if json_match:
                result = json.loads(json_match.group())
                return result
            else:
                return {"error": "无法解析 JSON 结果", "raw_output": result_text}

        except json.JSONDecodeError as e:
            return {"error": f"JSON 解析失败: {e}"}
        except Exception as e:
            return {"error": f"分析失败: {e}"}


def run_filter_step() -> tuple:
    """
    执行 Step 2: LLM 初筛
    返回 (news_list, llm_output)
    """
    # 获取新闻
    news_list = get_recent_news(limit=50)

    if not news_list:
        print("数据库中没有新闻，请先运行 --step fetch")
        return [], ""

    print(f"从数据库读取 {len(news_list)} 条新闻")

    # 调用 LLM 筛选
    analyzer = NewsAnalyzer()
    llm_output = analyzer.filter_news(news_list)

    return news_list, llm_output


def run_analyze_step(selected_ids: List[int]) -> Dict:
    """
    执行 Step 3: LLM 深度分析
    """
    if not selected_ids:
        print("没有选择新闻")
        return {}

    analyzer = NewsAnalyzer()
    result = analyzer.analyze_selected_news(selected_ids)

    return result


if __name__ == "__main__":
    # 测试
    news_list, output = run_filter_step()
    print("=" * 50)
    print(output)
