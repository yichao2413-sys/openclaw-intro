#!/usr/bin/env python3
"""
MRC Chart Parser v0.1
多模态研究助手 - 图表解析器
"""

import os
import sys
import json
import base64
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class ChartParser:
    """图表解析器主类"""
    
    def __init__(self, model: str = "qwen3-vl-plus"):
        self.model = model
        self.version = "0.1.0"
        self.iteration_log = PROJECT_ROOT / "data" / "iterations.jsonl"
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
        返回: (chart_type, confidence)
        """
        # TODO: 使用视觉模型识别图表类型
        # 目前使用简单的启发式规则
        
        # 这里应该调用视觉模型，但先返回占位
        return "bar_chart", 0.8
    
    def extract_data(self, image_path: str, chart_type: str) -> Dict:
        """
        从图表中提取数据
        返回结构化数据
        """
        # TODO: 使用多模态模型提取数据
        
        # 占位实现
        return {
            "chart_type": chart_type,
            "title": "示例图表",
            "x_axis": {"label": "X轴", "values": ["A", "B", "C"]},
            "y_axis": {"label": "Y轴", "values": [10, 20, 15]},
            "series": [{"name": "数据系列1", "values": [10, 20, 15]}]
        }
    
    def generate_plotly(self, data: Dict, output_path: str):
        """生成 Plotly 交互式图表"""
        
        plotly_code = f'''import plotly.graph_objects as go
import plotly.express as px

# 数据
labels = {data['x_axis']['values']}
values = {data['series'][0]['values']}

# 创建图表
fig = go.Figure(data=[
    go.Bar(
        x=labels,
        y=values,
        name='{data['series'][0]['name']}',
        marker_color='rgb(55, 83, 109)'
    )
])

# 布局
fig.update_layout(
    title='{data['title']}',
    xaxis_title='{data['x_axis']['label']}',
    yaxis_title='{data['y_axis']['label']}',
    template='plotly_white',
    hovermode='x unified'
)

# 保存为 HTML
fig.write_html("{output_path}")
print(f"图表已保存: {output_path}")

# 显示图表
fig.show()
'''
        
        return plotly_code
    
    def generate_matplotlib(self, data: Dict) -> str:
        """生成 Matplotlib 代码"""
        
        code = f'''import matplotlib.pyplot as plt
import numpy as np

# 数据
labels = {data['x_axis']['values']}
values = {data['series'][0]['values']}

# 创建图表
fig, ax = plt.subplots(figsize=(10, 6))

bars = ax.bar(labels, values, color='#37536D', alpha=0.8, edgecolor='black')

# 添加数值标签
for bar in bars:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height,
            f'{{height:.1f}}',
            ha='center', va='bottom')

# 设置标签
ax.set_xlabel('{data['x_axis']['label']}', fontsize=12)
ax.set_ylabel('{data['y_axis']['label']}', fontsize=12)
ax.set_title('{data['title']}', fontsize=14, fontweight='bold')

# 美化
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig('chart_output.png', dpi=300, bbox_inches='tight')
plt.show()
'''
        
        return code
    
    def parse(self, image_path: str, output_dir: str) -> Dict:
        """
        主解析流程
        """
        print(f"🔍 解析图表: {image_path}")
        
        try:
            # 1. 识别图表类型
            chart_type, confidence = self.identify_chart_type(image_path)
            print(f"📊 识别为: {chart_type} (置信度: {confidence:.2f})")
            
            # 2. 提取数据
            data = self.extract_data(image_path, chart_type)
            print(f"📈 提取数据点: {len(data.get('series', []))} 个系列")
            
            # 3. 生成输出
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # 生成 Plotly 代码
            plotly_code = self.generate_plotly(data, str(output_path / "interactive_chart.html"))
            with open(output_path / "plotly_code.py", "w", encoding="utf-8") as f:
                f.write(plotly_code)
            print(f"✅ 生成 Plotly 代码: {output_path / 'plotly_code.py'}")
            
            # 生成 Matplotlib 代码
            mpl_code = self.generate_matplotlib(data)
            with open(output_path / "matplotlib_code.py", "w", encoding="utf-8") as f:
                f.write(mpl_code)
            print(f"✅ 生成 Matplotlib 代码: {output_path / 'matplotlib_code.py'}")
            
            # 保存数据
            with open(output_path / "data.json", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"✅ 保存数据: {output_path / 'data.json'}")
            
            # 记录成功
            self.log_iteration(image_path, chart_type, True, "", 
                             {"confidence": confidence, "output_dir": str(output_path)})
            
            return {
                "success": True,
                "chart_type": chart_type,
                "data": data,
                "outputs": {
                    "plotly": str(output_path / "plotly_code.py"),
                    "matplotlib": str(output_path / "matplotlib_code.py"),
                    "data": str(output_path / "data.json")
                }
            }
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ 错误: {error_msg}")
            
            # 记录失败
            self.log_iteration(image_path, "unknown", False, error_msg)
            
            return {
                "success": False,
                "error": error_msg
            }


def main():
    parser = argparse.ArgumentParser(description="MRC Chart Parser - 图表解析器")
    parser.add_argument("--input", "-i", required=True, help="输入图片路径")
    parser.add_argument("--output", "-o", default="./outputs", help="输出目录")
    parser.add_argument("--model", default="qwen3-vl-plus", help="使用的视觉模型")
    
    args = parser.parse_args()
    
    # 创建解析器
    parser = ChartParser(model=args.model)
    
    # 执行解析
    result = parser.parse(args.input, args.output)
    
    # 输出结果
    if result["success"]:
        print("\n" + "="*50)
        print("✅ 解析完成!")
        print("="*50)
        print(f"图表类型: {result['chart_type']}")
        print(f"输出文件:")
        for key, path in result['outputs'].items():
            print(f"  - {key}: {path}")
    else:
        print("\n" + "="*50)
        print("❌ 解析失败")
        print("="*50)
        print(f"错误: {result['error']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
