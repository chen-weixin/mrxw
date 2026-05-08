#!/usr/bin/env python3
"""
新闻 Pipeline 主入口脚本

用法：
    python run_pipeline.py --step fetch    # Step 1: 获取新闻
    python run_pipeline.py --step filter   # Step 2: LLM 初筛
    python run_pipeline.py --step analyze  # Step 3: LLM 深度分析
    python run_pipeline.py --step video   # Step 4: 生成视频
    python run_pipeline.py --full         # 完整流程
"""

import sys
import os
import argparse
import re

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from news_pipeline.fetcher import fetch_and_save
from news_pipeline.analyzer import NewsAnalyzer, run_filter_step, run_analyze_step
from news_pipeline.database import get_recent_news, get_news_by_ids, init_database
from news_pipeline.video_generator import generate_video


def print_banner():
    """打印横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║              每日前瞻视频 - 新闻分析 Pipeline                  ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(banner)


def step_fetch():
    """Step 1: 获取新闻"""
    print("\n📰 Step 1: 获取新闻")
    print("=" * 50)

    count = fetch_and_save()

    print(f"\n✅ 获取完成，共 {count} 条新闻保存到数据库")


def step_filter():
    """Step 2: LLM 初筛"""
    print("\n🔍 Step 2: LLM 新闻初筛")
    print("=" * 50)

    # 获取新闻
    news_list, llm_output = run_filter_step()

    if not news_list:
        print("没有新闻可供分析")
        return None, None

    # 显示 LLM 筛选结果
    print("\n" + "=" * 50)
    print("📋 LLM 筛选结果:")
    print("=" * 50)
    print(llm_output)
    print("=" * 50)

    return news_list, llm_output


def parse_user_selection(llm_output: str, max_news: int) -> list:
    """解析用户选择"""
    print("\n" + "=" * 50)
    print("📝 请选择要深度分析的新闻编号")
    print("   格式如: 1, 3, 5 或 1-3（范围）")
    print(f"   可选范围: 1-{max_news}")
    print("=" * 50)

    while True:
        user_input = input("\n请输入编号 (q 退出): ").strip()

        if user_input.lower() == 'q':
            print("已退出")
            return []

        if not user_input:
            continue

        # 解析输入
        selected = set()

        # 处理范围格式如 "1-3"
        range_match = re.match(r'(\d+)-(\d+)', user_input)
        if range_match:
            start, end = int(range_match.group(1)), int(range_match.group(2))
            selected.update(range(start, end + 1))
        else:
            # 处理逗号分隔格式如 "1, 3, 5"
            for part in user_input.split(','):
                part = part.strip()
                if part.isdigit():
                    selected.add(int(part))

        # 验证选择
        valid = [s for s in selected if 1 <= s <= max_news]

        if valid:
            print(f"\n✅ 您选择了: {sorted(valid)}")
            return sorted(valid)

        print(f"⚠️ 输入无效，请输入 1-{max_news} 范围内的编号")


def step_analyze(selected_ids: list):
    """Step 3: LLM 深度分析"""
    if not selected_ids:
        print("没有选择新闻，跳过分析")
        return None

    print("\n🧠 Step 3: LLM 深度分析")
    print("=" * 50)
    print(f"分析新闻编号: {selected_ids}")
    print("正在调用 LLM 进行深度因果分析...")

    result = run_analyze_step(selected_ids)

    if "error" in result:
        print(f"❌ 分析失败: {result['error']}")
        return None

    # 显示分析结果摘要
    if "news_list" in result:
        print("\n✅ 分析完成！")
        print(f"共分析了 {len(result['news_list'])} 条新闻\n")

        for i, news in enumerate(result["news_list"]):
            print(f"--- 新闻 {i+1}: {news.get('title', '无标题')} ---")
            print(f"核心事实: {news.get('core_fact', 'N/A')[:50]}...")
            industries = news.get("industries", [])
            if industries:
                print(f"受益行业: {', '.join([ind['name'] for ind in industries[:3]])}")
            print()

    return result


def step_video(analysis_result: dict, selected_ids: list):
    """Step 4: 生成视频"""
    if not analysis_result:
        print("没有分析结果，跳过视频生成")
        return False

    print("\n🎬 Step 4: 生成视频")
    print("=" * 50)
    print("正在生成视频场景...")

    success = generate_video(analysis_result, selected_ids)

    if success:
        print("\n✅ 视频素材准备完成！")
        print("\n下一步：")
        print("  1. 检查 scenes/ 目录下的场景文件")
        print("  2. 运行渲染: cd /Users/chenweixin/claude/mrxw && npx hyperframes render --output daily-brief.mp4")
    else:
        print("\n❌ 视频生成失败")

    return success


def run_full_pipeline():
    """完整流程"""
    print_banner()

    # Step 1: 获取新闻
    step_fetch()

    # Step 2: LLM 初筛
    news_list, llm_output = step_filter()

    if news_list is None:
        return

    # 用户选择
    selected_ids = parse_user_selection(llm_output, len(news_list))

    if not selected_ids:
        print("未选择任何新闻，流程结束")
        return

    # Step 3: LLM 深度分析
    analysis_result = step_analyze(selected_ids)

    if not analysis_result:
        return

    # Step 4: 生成视频
    step_video(analysis_result, selected_ids)

    print("\n" + "=" * 50)
    print("🎉 Pipeline 执行完成!")
    print("=" * 50)


def main():
    parser = argparse.ArgumentParser(description="每日前瞻视频 Pipeline")
    parser.add_argument("--step", choices=["fetch", "filter", "analyze", "video"],
                        help="执行指定步骤")
    parser.add_argument("--full", action="store_true",
                        help="执行完整流程")
    parser.add_argument("--ids", type=str, default="",
                        help="直接指定要分析的新闻ID (逗号分隔)")

    args = parser.parse_args()

    print_banner()

    # 初始化数据库
    init_database()

    if args.full:
        run_full_pipeline()
        return

    if args.step == "fetch":
        step_fetch()

    elif args.step == "filter":
        news_list, llm_output = step_filter()
        if news_list:
            # 保存供后续使用
            with open("/tmp/llm_output.txt", "w") as f:
                f.write(llm_output)
            print(f"\n💡 LLM 输出已保存到 /tmp/llm_output.txt")
            print("运行 --step analyze 继续分析")

    elif args.step == "analyze":
        if args.ids:
            # 直接使用指定 ID
            selected_ids = [int(x.strip()) for x in args.ids.split(",")]
            result = step_analyze(selected_ids)
            if result:
                # 保存结果
                import json
                with open("/tmp/analysis_result.json", "w") as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                print(f"\n💡 分析结果已保存到 /tmp/analysis_result.json")
                print("运行 --step video 生成视频")
        else:
            print("请使用 --ids 指定新闻ID，或运行 --full 执行完整流程")

    elif args.step == "video":
        import json
        if os.path.exists("/tmp/analysis_result.json"):
            with open("/tmp/analysis_result.json") as f:
                result = json.load(f)
            step_video(result, [])
        else:
            print("请先运行 --step analyze 生成分析结果")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
