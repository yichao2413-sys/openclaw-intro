#!/usr/bin/env python3
"""
MRC 自我改进模块
分析迭代日志，自动优化系统
"""

import json
from pathlib import Path
from datetime import datetime
from collections import Counter


class SelfImprover:
    """自我改进引擎"""
    
    def __init__(self, project_root: str = None):
        if project_root is None:
            self.project_root = Path(__file__).parent.parent
        else:
            self.project_root = Path(project_root)
        
        self.iteration_log = self.project_root / "data" / "iterations.jsonl"
        self.improvement_log = self.project_root / "data" / "improvements.json"
        
    def load_iterations(self) -> list:
        """加载所有迭代记录"""
        if not self.iteration_log.exists():
            return []
        
        iterations = []
        with open(self.iteration_log, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        iterations.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return iterations
    
    def analyze_patterns(self) -> dict:
        """分析成功/失败模式"""
        iterations = self.load_iterations()
        
        if not iterations:
            return {"message": "暂无迭代数据"}
        
        # 统计
        total = len(iterations)
        successes = sum(1 for i in iterations if i.get("success"))
        failures = total - successes
        
        # 按图表类型统计
        chart_types = Counter(i.get("chart_type", "unknown") for i in iterations)
        
        # 常见错误
        errors = Counter(i.get("error", "") for i in iterations 
                        if not i.get("success") and i.get("error"))
        
        # 按版本统计
        versions = Counter(i.get("version", "unknown") for i in iterations)
        
        return {
            "total_iterations": total,
            "success_rate": successes / total if total > 0 else 0,
            "success_count": successes,
            "failure_count": failures,
            "chart_type_distribution": dict(chart_types),
            "common_errors": dict(errors.most_common(5)),
            "version_distribution": dict(versions)
        }
    
    def generate_suggestions(self) -> list:
        """基于分析生成改进建议"""
        analysis = self.analyze_patterns()
        suggestions = []
        
        if analysis.get("total_iterations", 0) == 0:
            return ["暂无数据，需要更多迭代来生成建议"]
        
        # 成功率分析
        success_rate = analysis.get("success_rate", 0)
        if success_rate < 0.5:
            suggestions.append(f"⚠️ 成功率较低 ({success_rate:.1%})，建议检查数据提取逻辑")
        elif success_rate < 0.8:
            suggestions.append(f"📈 成功率中等 ({success_rate:.1%})，有提升空间")
        else:
            suggestions.append(f"✅ 成功率良好 ({success_rate:.1%})")
        
        # 图表类型分析
        chart_types = analysis.get("chart_type_distribution", {})
        if "unknown" in chart_types:
            suggestions.append(f"🎯 有 {chart_types['unknown']} 个未知类型图表，需要增强类型识别")
        
        # 错误分析
        errors = analysis.get("common_errors", {})
        if errors:
            top_error = list(errors.keys())[0]
            suggestions.append(f"🔧 最常见错误: '{top_error[:50]}...'，建议针对性修复")
        
        return suggestions
    
    def update_prompts(self):
        """根据分析结果更新提示词（预留接口）"""
        # TODO: 根据失败案例自动调整提示词
        pass
    
    def report(self):
        """生成改进报告"""
        print("="*60)
        print("🔄 MRC 自我改进报告")
        print("="*60)
        
        analysis = self.analyze_patterns()
        
        print(f"\n📊 迭代统计:")
        print(f"  总迭代次数: {analysis.get('total_iterations', 0)}")
        print(f"  成功率: {analysis.get('success_rate', 0):.1%}")
        print(f"  成功: {analysis.get('success_count', 0)}")
        print(f"  失败: {analysis.get('failure_count', 0)}")
        
        print(f"\n📈 图表类型分布:")
        for chart_type, count in analysis.get("chart_type_distribution", {}).items():
            print(f"  - {chart_type}: {count}")
        
        if analysis.get("common_errors"):
            print(f"\n❌ 常见错误:")
            for error, count in list(analysis.get("common_errors", {}).items())[:3]:
                print(f"  - ({count}次) {error[:60]}...")
        
        print(f"\n💡 改进建议:")
        for suggestion in self.generate_suggestions():
            print(f"  {suggestion}")
        
        print("\n" + "="*60)
        
        # 保存报告
        report = {
            "timestamp": datetime.now().isoformat(),
            "analysis": analysis,
            "suggestions": self.generate_suggestions()
        }
        
        self.improvement_log.parent.mkdir(parents=True, exist_ok=True)
        with open(self.improvement_log, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        return report


def main():
    """命令行入口"""
    improver = SelfImprover()
    improver.report()


if __name__ == "__main__":
    main()
