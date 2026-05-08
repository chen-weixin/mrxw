"""视频生成模块 - 根据分析结果生成视频场景"""

import os
import subprocess
import json
from datetime import datetime
from typing import Dict, List
from .config import SCENES_DIR, AUDIO_DIR, MOSS_CLONE_SCRIPT


class VideoGenerator:
    """视频生成器"""

    def __init__(self):
        self.scenes_dir = SCENES_DIR
        self.audio_dir = AUDIO_DIR
        self.narration_template = """
欢迎来到鑫观点市场前瞻，每天五分钟，纵览市场动态，把握投资机会，让我们开始吧。

{narration_content}

请持续关注鑫观点，明天再见。
"""

    def generate_narration_script(self, analysis_result: Dict) -> str:
        """根据分析结果生成配音脚本"""
        if "news_list" not in analysis_result:
            return ""

        script_parts = []

        for i, news in enumerate(analysis_result["news_list"]):
            vm = news.get("video_material", {})
            title = news.get("title", "")

            # 生成这条新闻的配音
            intro = vm.get("intro", "")
            core_point = vm.get("core_point", "")
            summary = vm.get("summary", "")

            # 提取行业信息
            industries = news.get("industries", [])
            benefited = news.get("companies", {}).get("benefited", [])

            script = f"{intro}。"
            if core_point:
                script += f" {core_point}。"
            if industries:
                industry_names = "、".join([ind["name"] for ind in industries[:3]])
                script += f" {industry_names}相关板块值得关注。"
            if benefited:
                company_names = "、".join(benefited[:3])
                script += f" {company_names}等企业有望受益。"
            if summary:
                script += f" {summary}。"

            script_parts.append(script)

        return "\n\n".join(script_parts)

    def generate_audio(self, script: str, output_file: str) -> bool:
        """调用 MOSS-TTS 生成音频"""
        if not script.strip():
            print("配音脚本为空")
            return False

        try:
            # 写入临时脚本文件
            script_file = os.path.join(self.audio_dir, "_temp_script.txt")
            with open(script_file, "w", encoding="utf-8") as f:
                f.write(script)

            # 调用 moss_clone.sh
            result = subprocess.run(
                ["bash", MOSS_CLONE_SCRIPT, "--file", script_file, "--output", output_file],
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode == 0:
                print(f"音频生成成功: {output_file}")
                return True
            else:
                print(f"音频生成失败: {result.stderr}")
                return False

        except Exception as e:
            print(f"生成音频异常: {e}")
            return False
        finally:
            # 清理临时文件
            if os.path.exists(script_file):
                os.remove(script_file)

    def update_scene_html(self, news_data: Dict, scene_file: str, index: int):
        """更新场景 HTML 文件"""
        if not os.path.exists(scene_file):
            print(f"场景文件不存在: {scene_file}")
            return False

        # 读取原文件
        with open(scene_file, "r", encoding="utf-8") as f:
            content = f.read()

        # 提取内容
        title = news_data.get("title", "新闻标题")
        core_fact = news_data.get("core_fact", "")
        causality = news_data.get("causality", {})
        industries = news_data.get("industries", [])
        companies = news_data.get("companies", {})

        # 构建新的内容
        direct_impact = causality.get("direct_impact", "")
        transmission_path = causality.get("transmission_path", "")
        deep_logic = causality.get("deep_logic", "")

        benefited = companies.get("benefited", [])
        harmed = companies.get("harmed", [])

        # 构建行业和企业文本
        industries_text = ""
        for ind in industries:
            direction_icon = "🔺" if ind.get("direction") == "利好" else "⚠️"
            industries_text += f"{direction_icon} {ind.get('name', '')}："
            industries_text += f"{ind.get('direction', '')} | {ind.get('degree', '')}级\n"

        companies_text = ""
        if benefited:
            companies_text += f"<span class=\"up\">🔺 受益：</span>{'、'.join(benefited)}\n"
        if harmed:
            companies_text += f"<span class=\"down\">⚠️ 受压：</span>{'、'.join(harmed)}"

        # 构建影响逻辑文本
        impact_text = f"<strong>直接影响：</strong>{direct_impact}\n"
        impact_text += f"<strong>传导路径：</strong>{transmission_path}\n"
        impact_text += f"<strong>深层逻辑：</strong>{deep_logic}"

        # 替换内容
        # 标题
        content = content.replace(
            '<div class="page-title" id="page-title">具身智能下半场</div>',
            f'<div class="page-title" id="page-title">{title}</div>'
        )

        # 替换页面标题（通用匹配）
        content = content.replace(
            'page-title">具身智能下半场</div>',
            f'page-title">{title}</div>'
        )

        # 替换内容块
        section1_content = f"{core_fact}"
        section2_content = impact_text
        section3_content = companies_text

        # 替换 source
        source_text = f"来源：AI分析"
        content = content.replace(
            '<div class="source">来源：权威机构</div>',
            f'<div class="source">{source_text}</div>'
        )

        # 替换页码
        content = content.replace(
            'page-indicator">04 / 04</div>',
            f'page-indicator">{index:02d} / {index:02d}</div>'
        )
        content = content.replace(
            'ghost-num">04</div>',
            f'ghost-num">{index:02d}</div>'
        )

        # 写回文件
        with open(scene_file, "w", encoding="utf-8") as f:
            f.write(content)

        return True

    def generate_from_analysis(self, analysis_result: Dict, news_ids: List[int]) -> bool:
        """根据分析结果生成视频"""
        if "news_list" not in analysis_result:
            print("分析结果中没有 news_list")
            return False

        news_list = analysis_result["news_list"]

        # 生成 hook 场景（保持不变）

        # 更新新闻场景
        for i, news in enumerate(news_list[:4]):  # 最多4条
            scene_file = os.path.join(self.scenes_dir, f"scene-n{i+1}.html")
            self.update_scene_html(news, scene_file, i + 1)
            print(f"已更新场景: scene-n{i+1}.html")

        # 生成配音
        narration_script = self.generate_narration_script(analysis_result)

        # 保存配音脚本
        script_file = os.path.join(self.audio_dir, "narration_script.txt")
        with open(script_file, "w", encoding="utf-8") as f:
            f.write(narration_script)
        print(f"配音脚本已保存: {script_file}")

        # 生成完整配音
        hook_script = "欢迎来到鑫观点市场前瞻，每天五分钟，纵览市场动态，把握投资机会，让我们开始吧。"
        news_script = narration_script.replace("\n\n", "。")

        full_script = f"{hook_script}\n\n{news_script}\n\n请持续关注鑫观点，明天再见。"

        # 调用 MOSS 生成
        output_file = os.path.join(self.audio_dir, "full_narration.wav")
        self.generate_audio(full_script, output_file)

        print("视频素材准备完成")
        return True


def generate_video(analysis_result: Dict, news_ids: List[int]) -> bool:
    """生成视频的入口函数"""
    generator = VideoGenerator()
    return generator.generate_from_analysis(analysis_result, news_ids)


if __name__ == "__main__":
    # 测试
    test_result = {
        "news_list": [
            {
                "title": "测试新闻",
                "core_fact": "这是一个测试",
                "causality": {
                    "direct_impact": "测试影响",
                    "transmission_path": "测试路径",
                    "deep_logic": "测试逻辑"
                },
                "industries": [
                    {"name": "测试行业", "direction": "利好", "degree": "高"}
                ],
                "companies": {
                    "benefited": ["测试企业A"],
                    "harmed": []
                },
                "video_material": {
                    "intro": "测试开场",
                    "core_point": "测试核心",
                    "summary": "测试总结"
                }
            }
        ]
    }

    generator = VideoGenerator()
    script = generator.generate_narration_script(test_result)
    print("生成的配音脚本:")
    print(script)
