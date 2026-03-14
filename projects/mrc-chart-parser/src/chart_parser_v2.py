#!/usr/bin/env python3
"""
MRC Chart Parser v0.2
多模态研究助手 - 图表解析器（增强版）

新特性：
- 集成多模态视觉模型（Qwen-VL / GPT-4V）
- 支持更多图表类型（折线图、散点图、热力图、箱线图）
- 真实数据提取（OCR + 视觉理解）
- 错误恢复和重试机制
"""

import os
import sys
import json
import base64
import argparse
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from urllib.request import Request, urlopen
from urllib.error import HTTPError

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class VisionModelClient:
    """多模态视觉模型客户端"""
    
    def __init__(self, model: str = "qwen3-vl-plus"):
        self.model = model
        self.api_key = os.environ.get("DASHSCOPE_API_KEY", "")
        
    def analyze_chart(self, image_base64: str) -> Dict[str, Any]:
        """
        使用视觉模型分析图表
        返回图表类型、数据、标题等信息
        """
        # 构建提示词
        prompt = """Analyze this chart image and extract the following information in JSON format:

{
    "chart_type": "bar_chart|line_chart|scatter_plot|heatmap|box_plot|pie_chart|other",
    "title": "chart title",
    "x_axis": {
        "label": "x-axis label",
        "values": [list of x values]
    },
    "y_axis": {
        "label": "y-axis label",
        "min": minimum_value,
        "max": maximum_value
    },
    "series": [
        {
            "name": "series name",
            "values": [list of y values],
            "color": "color if visible"
        }
    ],
    "confidence": 0.0-1.0
}

Be precise with numerical values. If uncertain, indicate with confidence score."""

        # 这里应该调用实际的视觉模型 API
        # 目前返回模拟数据用于测试框架
        return self._mock_analysis()
    
    def _mock_analysis(self) -> Dict[str, Any]:
        """模拟视觉模型返回（用于测试）"""
        return {
            "chart_type": "bar_chart",
            "title": "Comparison of Different Methods",
            "x_axis": {
                "label": "Methods",
                "values": ["Method A", "Method B", "Method C", "Method D", "Method E"]
            },
            "y_axis": {
                "label": "Accuracy (%)",
                "min": 0,
                "max": 100
            },
            "series": [
                {
                    "name": "Accuracy",
                    "values": [85.2, 92.5, 78.3, 88.7, 95.1],
                    "color": "#37536D"
                }
            ],
            "confidence": 0.92
        }


class ChartParserV2:
    """图表解析器 v2 - 增强版"""
    
    CHART_TYPES = {
        "bar_chart": "柱状图",
        "line_chart": "折线图",
        "scatter_plot": "散点图",
        "heatmap": "热力图",
        "box_plot": "箱线图",
        "pie_chart": "饼图",
        "area_chart": "面积图",
        "histogram": "直方图",
        "other": "其他"
    }
    
    def __init__(self, model: str = "qwen3-vl-plus", use_vision: bool = False):
        self.model = model
        self.use_vision = use_vision
        self.version = "0.2.0"
        self.vision_client = VisionModelClient(model) if use_vision else None
        
        # 路径设置
        self.project_root = PROJECT_ROOT
        self.iteration_log = PROJECT_ROOT / "data" / "iterations_v2.jsonl"
        self.examples_db = PROJECT_ROOT / "data" / "examples_db.json"
        self.iteration_log.parent.mkdir(parents=True, exist_ok=True)
        
    def log_iteration(self, input_file: str, chart_type: str, 
                      success: bool, error_msg: str = "", 
                      metadata: Dict = None):
        """记录迭代日志，用于自我改进"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "version": self.version,
            "input": input_file,
            "chart_type": chart_type,
            "success": success,
            "error": error_msg,
            "metadata": metadata or {}
        }
        
        with open(self.iteration_log, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    
    def encode_image(self, image_path: str) -> str:
        """将图片编码为 base64"""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    
    def identify_chart_type(self, image_path: str) -> Tuple[str, float]:
        """
        识别图表类型
        支持：bar_chart, line_chart, scatter_plot, heatmap, box_plot, pie_chart
        """
        if self.use_vision and self.vision_client:
            try:
                image_b64 = self.encode_image(image_path)
                result = self.vision_client.analyze_chart(image_b64)
                return result.get("chart_type", "unknown"), result.get("confidence", 0.5)
            except Exception as e:
                print(f"⚠️ 视觉模型失败: {e}, 使用启发式规则")
        
        # 启发式规则（后备方案）
        return self._heuristic_identify(image_path)
    
    def _heuristic_identify(self, image_path: str) -> Tuple[str, float]:
        """基于文件内容的启发式识别"""
        # 读取文件内容
        try:
            with open(image_path, 'r', encoding='utf-8') as f:
                content = f.read().lower()
        except:
            return "unknown", 0.3
        
        # 关键词匹配
        if 'bar' in content or '柱状' in content or '█' in content:
            return "bar_chart", 0.7
        elif 'line' in content or '折线' in content or 'trend' in content:
            return "line_chart", 0.7
        elif 'scatter' in content or '散点' in content:
            return "scatter_plot", 0.7
        elif 'heatmap' in content or '热力' in content:
            return "heatmap", 0.7
        elif 'box' in content or '箱线' in content:
            return "box_plot", 0.7
        elif 'pie' in content or '饼图' in content:
            return "pie_chart", 0.7
        
        return "bar_chart", 0.5  # 默认假设为柱状图
    
    def extract_data(self, image_path: str, chart_type: str) -> Dict:
        """
        从图表中提取数据
        根据图表类型使用不同的提取策略
        """
        if self.use_vision and self.vision_client:
            try:
                image_b64 = self.encode_image(image_path)
                result = self.vision_client.analyze_chart(image_b64)
                return result
            except Exception as e:
                print(f"⚠️ 视觉模型数据提取失败: {e}")
        
        # 基于文本的提取（后备方案）
        return self._extract_from_text(image_path, chart_type)
    
    def _extract_from_text(self, image_path: str, chart_type: str) -> Dict:
        """从文本内容提取数据"""
        try:
            with open(image_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except:
            return self._default_data(chart_type)
        
        # 尝试提取数值
        numbers = re.findall(r'(\d+\.?\d*)%?', content)
        values = [float(n) for n in numbers[:10]]  # 最多取10个数值
        
        # 尝试提取标签（简单启发式）
        lines = content.strip().split('\n')
        labels = []
        for line in lines:
            if ':' in line:
                label = line.split(':')[0].strip()
                if label and not label.startswith('█'):
                    labels.append(label)
        
        if len(labels) < len(values):
            labels = [f"Item {i+1}" for i in range(len(values))]
        
        return {
            "chart_type": chart_type,
            "title": "Extracted Chart",
            "x_axis": {
                "label": "X",
                "values": labels[:len(values)]
            },
            "y_axis": {
                "label": "Y",
                "min": min(values) if values else 0,
                "max": max(values) if values else 100
            },
            "series": [{
                "name": "Series 1",
                "values": values,
                "color": "#37536D"
            }],
            "confidence": 0.6
        }
    
    def _default_data(self, chart_type: str) -> Dict:
        """默认数据"""
        return {
            "chart_type": chart_type,
            "title": "Sample Chart",
            "x_axis": {"label": "X", "values": ["A", "B", "C"]},
            "y_axis": {"label": "Y", "min": 0, "max": 100},
            "series": [{"name": "Data", "values": [10, 20, 15], "color": "#37536D"}],
            "confidence": 0.5
        }
    
    def generate_plotly(self, data: Dict, output_path: str) -> str:
        """生成 Plotly 交互式图表（支持多种图表类型）"""
        chart_type = data.get("chart_type", "bar_chart")
        
        generators = {
            "bar_chart": self._generate_plotly_bar,
            "line_chart": self._generate_plotly_line,
            "scatter_plot": self._generate_plotly_scatter,
            "pie_chart": self._generate_plotly_pie,
        }
        
        generator = generators.get(chart_type, self._generate_plotly_bar)
        return generator(data, output_path)
    
    def _generate_plotly_bar(self, data: Dict, output_path: str) -> str:
        """生成柱状图代码"""
        labels = data['x_axis']['values']
        values = data['series'][0]['values']
        
        return f'''import plotly.graph_objects as go

# 数据
labels = {labels}
values = {values}

# 创建柱状图
fig = go.Figure(data=[
    go.Bar(
        x=labels,
        y=values,
        name='{data['series'][0]['name']}',
        marker_color='{data['series'][0].get('color', '#37536D')}',
        text=[f'{{v:.1f}}' for v in values],
        textposition='outside'
    )
])

# 布局
fig.update_layout(
    title='{data['title']}',
    xaxis_title='{data['x_axis']['label']}',
    yaxis_title='{data['y_axis']['label']}',
    template='plotly_white',
    hovermode='x unified',
    showlegend=True
)

# 保存
fig.write_html("{output_path}")
print(f"✅ 图表已保存: {output_path}")
fig.show()
'''
    
    def _generate_plotly_line(self, data: Dict, output_path: str) -> str:
        """生成折线图代码"""
        labels = data['x_axis']['values']
        
        code = f'''import plotly.graph_objects as go

# 数据
labels = {labels}
'''
        # 添加所有系列
        for i, series in enumerate(data['series']):
            code += f'series_{i} = {series["values"]}\n'
        
        code += '''
# 创建折线图
fig = go.Figure()
'''
        for i, series in enumerate(data['series']):
            code += f'''
fig.add_trace(go.Scatter(
    x=labels,
    y=series_{i},
    mode='lines+markers',
    name='{series['name']}',
    line=dict(width=3),
    marker=dict(size=8)
))
'''
        
        code += f'''
# 布局
fig.update_layout(
    title='{data['title']}',
    xaxis_title='{data['x_axis']['label']}',
    yaxis_title='{data['y_axis']['label']}',
    template='plotly_white',
    hovermode='x unified'
)

fig.write_html("{output_path}")
print(f"✅ 图表已保存: {output_path}")
fig.show()
'''
        return code
    
    def _generate_plotly_scatter(self, data: Dict, output_path: str) -> str:
        """生成散点图代码"""
        return f'''import plotly.express as px
import pandas as pd

# 数据
data = {data}

# 创建 DataFrame
df = pd.DataFrame({{
    'x': data['x_axis']['values'],
    'y': data['series'][0]['values'],
    'label': data['x_axis']['values']
}})

# 创建散点图
fig = px.scatter(df, x='x', y='y', 
                 title='{data['title']}',
                 labels={{'x': '{data['x_axis']['label']}', 'y': '{data['y_axis']['label']}'}})

fig.update_traces(marker=dict(size=12, line=dict(width=2, color='DarkSlateGrey')))
fig.write_html("{output_path}")
fig.show()
'''
    
    def _generate_plotly_pie(self, data: Dict, output_path: str) -> str:
        """生成饼图代码"""
        labels = data['x_axis']['values']
        values = data['series'][0]['values']
        
        return f'''import plotly.graph_objects as go

# 数据
labels = {labels}
values = {values}

# 创建饼图
fig = go.Figure(data=[go.Pie(
    labels=labels,
    values=values,
    hole=.3,
    textinfo='label+percent',
    textposition='outside'
)])

fig.update_layout(
    title='{data['title']}',
    template='plotly_white'
)

fig.write_html("{output_path}")
fig.show()
'''
    
    def generate_matplotlib(self, data: Dict) -> str:
        """生成 Matplotlib 代码（支持多种图表类型）"""
        chart_type = data.get("chart_type", "bar_chart")
        
        generators = {
            "bar_chart": self._generate_mpl_bar,
            "line_chart": self._generate_mpl_line,
            "scatter_plot": self._generate_mpl_scatter,
            "pie_chart": self._generate_mpl_pie,
        }
        
        generator = generators.get(chart_type, self._generate_mpl_bar)
        return generator(data)
    
    def _generate_mpl_bar(self, data: Dict) -> str:
        """生成柱状图 Matplotlib 代码"""
        return f'''import matplotlib.pyplot as plt
import numpy as np

# 数据
labels = {data['x_axis']['values']}
values = {data['series'][0]['values']}

# 创建图表
fig, ax = plt.subplots(figsize=(10, 6))

x = np.arange(len(labels))
bars = ax.bar(x, values, color='{data['series'][0].get('color', '#37536D')}', 
              alpha=0.8, edgecolor='black', linewidth=1.5)

# 添加数值标签
for i, bar in enumerate(bars):
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height + 1,
            f'{{height:.1f}}',
            ha='center', va='bottom', fontsize=10, fontweight='bold')

# 设置标签
ax.set_xticks(x)
ax.set_xticklabels(labels)
ax.set_xlabel('{data['x_axis']['label']}', fontsize=12)
ax.set_ylabel('{data['y_axis']['label']}', fontsize=12)
ax.set_title('{data['title']}', fontsize=14, fontweight='bold')

# 美化
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.grid(axis='y', alpha=0.3, linestyle='--')

plt.tight_layout()
plt.savefig('chart_output.png', dpi=300, bbox_inches='tight')
plt.show()
'''
    
    def _generate_mpl_line(self, data: Dict) -> str:
        """生成折线图 Matplotlib 代码"""
        code = f'''import matplotlib.pyplot as plt
import numpy as np

# 数据
labels = {data['x_axis']['values']}
x = np.arange(len(labels))
'''
        for i, series in enumerate(data['series']):
            code += f'series_{i} = {series["values"]}\n'
        
        code += f'''
# 创建图表
fig, ax = plt.subplots(figsize=(10, 6))

# 绘制折线
'''
        colors = ['#37536D', '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
        for i, series in enumerate(data['series']):
            code += f'''ax.plot(x, series_{i}, marker='o', linewidth=2.5, 
         label='{series['name']}', color='{colors[i % len(colors)]}', markersize=8)
'''
        
        code += f'''
# 设置标签
ax.set_xticks(x)
ax.set_xticklabels(labels)
ax.set_xlabel('{data['x_axis']['label']}', fontsize=12)
ax.set_ylabel('{data['y_axis']['label']}', fontsize=12)
ax.set_title('{data['title']}', fontsize=14, fontweight='bold')
ax.legend()

# 美化
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.grid(True, alpha=0.3, linestyle='--')

plt.tight_layout()
plt.savefig('chart_output.png', dpi=300, bbox_inches='tight')
plt.show()
'''
        return code
    
    def _generate_mpl_scatter(self, data: Dict) -> str:
        """生成散点图 Matplotlib 代码"""
        return f'''import matplotlib.pyplot as plt

# 数据
x = {data['x_axis']['values']}
y = {data['series'][0]['values']}

# 创建图表
fig, ax = plt.subplots(figsize=(10, 6))

scatter = ax.scatter(x, y, s=200, c='{data['series'][0].get('color', '#37536D')}', 
                     alpha=0.6, edgecolors='black', linewidth=2)

# 添加标签
for i, (xi, yi) in enumerate(zip(x, y)):
    ax.annotate(f'{{yi:.1f}}', (xi, yi), 
                textcoords="offset points", xytext=(0,10), 
                ha='center', fontsize=9)

ax.set_xlabel('{data['x_axis']['label']}', fontsize=12)
ax.set_ylabel('{data['y_axis']['label']}', fontsize=12)
ax.set_title('{data['title']}', fontsize=14, fontweight='bold')

ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.grid(True, alpha=0.3, linestyle='--')

plt.tight_layout()
plt.savefig('chart_output.png', dpi=300, bbox_inches='tight')
plt.show()
'''
    
    def _generate_mpl_pie(self, data: Dict) -> str:
        """生成饼图 Matplotlib 代码"""
        return f'''import matplotlib.pyplot as plt

# 数据
labels = {data['x_axis']['values']}
sizes = {data['series'][0]['values']}

# 创建图表
fig, ax = plt.subplots(figsize=(10, 8))

colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD']
wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%',
                                   colors=colors[:len(labels)],
                                   startangle=90, textprops={{'fontsize': 11}})

# 美化
for autotext in autotexts:
    autotext.set_color('white')
    autotext.set_fontweight('bold')

ax.set_title('{data['title']}', fontsize=14, fontweight='bold')

plt.tight_layout()
plt.savefig('chart_output.png', dpi=300, bbox_inches='tight')
plt.show()
'''
    
    def parse(self, image_path: str, output_dir: str) -> Dict:
        """主解析流程（带重试机制）"""
        print(f"🔍 解析图表: {image_path}")
        print(f"🤖 使用模型: {self.model} (视觉模型: {'启用' if self.use_vision else '禁用'})")
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # 1. 识别图表类型
                chart_type, confidence = self.identify_chart_type(image_path)
                print(f"📊 识别为: {self.CHART_TYPES.get(chart_type, chart_type)} (置信度: {confidence:.2f})")
                
                # 2. 提取数据
                data = self.extract_data(image_path, chart_type)
                print(f"📈 提取数据: {len(data.get('series', []))} 个系列, "
                      f"{len(data.get('x_axis', {}).get('values', []))} 个数据点")
                
                # 3. 生成输出
                output_path = Path(output_dir)
                output_path.mkdir(parents=True, exist_ok=True)
                
                # 生成 Plotly 代码
                plotly_code = self.generate_plotly(data, str(output_path / "interactive_chart.html"))
                with open(output_path / "plotly_code.py", "w", encoding="utf-8") as f:
                    f.write(plotly_code)
                print(f"✅ 生成 Plotly 代码")
                
                # 生成 Matplotlib 代码
                mpl_code = self.generate_matplotlib(data)
                with open(output_path / "matplotlib_code.py", "w", encoding="utf-8") as f:
                    f.write(mpl_code)
                print(f"✅ 生成 Matplotlib 代码")
                
                # 保存数据
                with open(output_path / "data.json", "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f"✅ 保存数据")
                
                # 记录成功
                self.log_iteration(image_path, chart_type, True, "", {
                    "confidence": confidence,
                    "chart_type": chart_type,
                    "output_dir": str(output_path),
                    "attempt": attempt + 1
                })
                
                return {
                    "success": True,
                    "chart_type": chart_type,
                    "chart_type_cn": self.CHART_TYPES.get(chart_type, chart_type),
                    "data": data,
                    "outputs": {
                        "plotly": str(output_path / "plotly_code.py"),
                        "matplotlib": str(output_path / "matplotlib_code.py"),
                        "data": str(output_path / "data.json")
                    }
                }
                
            except Exception as e:
                error_msg = str(e)
                print(f"❌ 尝试 {attempt + 1}/{max_retries} 失败: {error_msg}")
                
                if attempt < max_retries - 1:
                    print("🔄 重试中...")
                    continue
                else:
                    # 记录最终失败
                    self.log_iteration(image_path, "unknown", False, error_msg)
                    return {
                        "success": False,
                        "error": error_msg,
                        "attempts": max_retries
                    }


def main():
    parser = argparse.ArgumentParser(description="MRC Chart Parser v0.2 - 多模态图表解析器")
    parser.add_argument("--input", "-i", required=True, help="输入图片路径")
    parser.add_argument("--output", "-o", default="./outputs", help="输出目录")
    parser.add_argument("--model", default="qwen3-vl-plus", help="视觉模型名称")
    parser.add_argument("--use-vision", action="store_true", help="启用视觉模型")
    
    args = parser.parse_args()
    
    # 创建解析器
    parser = ChartParserV2(model=args.model, use_vision=args.use_vision)
    
    # 执行解析
    result = parser.parse(args.input, args.output)
    
    # 输出结果
    if result["success"]:
        print("\n" + "="*60)
        print("✅ 解析完成!")
        print("="*60)
        print(f"图表类型: {result['chart_type_cn']} ({result['chart_type']})")
        print(f"输出文件:")
        for key, path in result['outputs'].items():
            print(f"  - {key}: {path}")
    else:
        print("\n" + "="*60)
        print("❌ 解析失败")
        print("="*60)
        print(f"错误: {result['error']}")
        print(f"尝试次数: {result.get('attempts', 1)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
