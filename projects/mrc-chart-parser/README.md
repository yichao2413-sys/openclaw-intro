# MRC Chart Parser - 多模态研究助手

## 项目目标
自动解析学术论文中的图表，提取数据并生成交互式可视化 + 可执行代码。

## 版本迭代

### v0.2 - 增强版 ✅
- [x] 支持 4 种图表类型：柱状图、折线图、散点图、饼图
- [x] 多模态视觉模型接口（预留）
- [x] 智能图表类型识别（启发式 + 视觉模型）
- [x] 重试机制（3次自动重试）
- [x] 多系列数据支持
- [x] 中英文图表类型显示

### v0.1 - MVP ✅
- [x] 基础架构
- [x] 图表类型识别
- [x] 数据提取
- [x] 生成 Plotly/Matplotlib 代码
- [x] 自我迭代机制

### v0.3 - 计划中
- [ ] 接入真实视觉模型（Qwen-VL）
- [ ] PDF 图表自动提取
- [ ] 跨论文图表对比
- [ ] 异常检测与修正

## 支持的图表类型

| 类型 | 英文 | 状态 |
|-----|------|------|
| 柱状图 | bar_chart | ✅ |
| 折线图 | line_chart | ✅ |
| 散点图 | scatter_plot | ✅ |
| 饼图 | pie_chart | ✅ |
| 热力图 | heatmap | 📝 |
| 箱线图 | box_plot | 📝 |

## 使用方式

### 基础用法
```bash
# 解析图表
python src/chart_parser_v2.py --input chart.txt --output ./outputs/

# 启用视觉模型（需要 API key）
python src/chart_parser_v2.py --input chart.png --use-vision --output ./outputs/
```

### 查看改进报告
```bash
python src/self_improve.py
```

## 项目结构
```
mrc-chart-parser/
├── src/
│   ├── chart_parser.py       # v0.1 基础版
│   ├── chart_parser_v2.py    # v0.2 增强版 ⭐
│   └── self_improve.py       # 自我改进模块
├── data/
│   ├── iterations.jsonl      # v0.1 迭代日志
│   ├── iterations_v2.jsonl   # v0.2 迭代日志
│   └── examples_db.json      # 示例数据库
├── outputs/                  # 输出目录
├── tests/                    # 测试数据
│   ├── sample_chart.txt      # 柱状图示例
│   ├── line_chart_sample.txt # 折线图示例
│   └── scatter_sample.txt    # 散点图示例
└── README.md
```

## 输出示例

解析后会生成三个文件：
1. `plotly_code.py` - 交互式 HTML 图表代码
2. `matplotlib_code.py` - 静态图片代码
3. `data.json` - 提取的结构化数据

## 技术栈
- Python 3.8+
- Plotly (交互可视化)
- Matplotlib (静态图表)
- 多模态视觉模型接口 (预留)

## 自我迭代机制

每次运行自动记录：
- 输入文件
- 识别的图表类型
- 成功率/失败原因
- 置信度分数

通过 `self_improve.py` 生成改进报告，分析：
- 成功率趋势
- 常见错误类型
- 图表类型分布
- 改进建议

---

**当前版本**: v0.2.0  
**最后更新**: 2026-03-15  
*Created by OpenClaw AI Assistant*
