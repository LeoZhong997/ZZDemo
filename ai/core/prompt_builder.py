"""
Prompt 构建器
提供 Prompt 模板构建、数据注入、模板渲染功能
"""
from typing import Dict, Any, List, Optional
import json
import logging

from ai.config import get_ai_config

logger = logging.getLogger(__name__)


class PromptBuilder:
    """
    Prompt 构建器
    
    功能：
    - 构建各类 Prompt 模板
    - 数据注入
    - 模板渲染
    """
    
    def __init__(self):
        """初始化，从配置读取系统提示词"""
        self.config = get_ai_config('prompt', {})
        self.max_context_length = self.config.get('max_context_length', 8000)
        self._system_prompt = self.config.get('system_prompt', self._get_default_system_prompt())
    
    def _get_default_system_prompt(self) -> str:
        """获取默认系统提示词"""
        return """你是一个专业的外卖经营分析助手，具备以下能力：

1. **数据分析**：能够分析门店营收、订单量、转化率等核心经营指标
2. **对比分析**：能够进行门店对比、平台对比，找出差异和问题
3. **异常诊断**：能够识别数据异常并提供可能的原因分析
4. **趋势预测**：能够基于历史数据分析趋势
5. **决策建议**：能够提供可执行的运营改进建议

回答要求：
- 基于数据事实进行分析
- 提供具体数字支撑观点
- 建议要可落地执行
- 语言简洁专业
- 按优先级排序建议"""
    
    def get_system_prompt(self) -> str:
        """获取系统提示词"""
        return self._system_prompt
    
    def build_diagnosis_prompt(self,
                                store_ranking: Dict,
                                platform_comparison: Dict,
                                anomalies: List[Dict],
                                period: str,
                                summary_stats: Dict = None) -> str:
        """
        构建诊断报告 Prompt
        
        Args:
            store_ranking: 门店排名数据
            platform_comparison: 平台对比数据
            anomalies: 异常列表
            period: 分析周期
            summary_stats: 摘要统计
            
        Returns:
            构建好的 Prompt 字符串
        """
        # 格式化门店排名
        store_ranking_str = self._format_store_ranking(store_ranking)
        
        # 格式化平台对比
        platform_comparison_str = self._format_platform_comparison(platform_comparison)
        
        # 格式化异常
        anomalies_str = self._format_anomalies(anomalies)
        
        # 格式化摘要统计
        summary_str = self._format_summary_stats(summary_stats) if summary_stats else ""
        
        prompt = f"""请根据以下数据分析经营状况并生成诊断报告。

## 分析周期
{period}

{summary_str}
## 门店表现排名 (Top 10)
{store_ranking_str}

## 平台对比分析
{platform_comparison_str}

## 检测到的异常
{anomalies_str}

## 请输出以下内容：

### 1. 整体经营概况
（总结核心指标表现，用数据说明）

### 2. 门店分析
（分析表现最好和需改进的门店，说明原因）

### 3. 平台分析
（对比各平台表现，给出差异化策略建议）

### 4. 问题诊断
（分析异常原因，深入挖掘潜在问题）

### 5. 改进建议
（3-5条可执行建议，按优先级排序，每条建议说明预期效果）"""
        
        return prompt
    
    def build_prediction_prompt(self,
                                 historical_data: List[Dict],
                                 predictions: List[Dict],
                                 trend: Dict,
                                 metric: str = 'actual_income') -> str:
        """
        构建预测分析 Prompt
        
        Args:
            historical_data: 历史数据
            predictions: 预测数据
            trend: 趋势信息
            metric: 分析指标
            
        Returns:
            构建好的 Prompt
        """
        # 格式化历史数据
        historical_str = self._format_time_series(historical_data, "历史数据", metric)
        
        # 格式化预测数据
        predictions_str = self._format_time_series(predictions, "预测数据", metric)
        
        # 格式化趋势信息
        trend_str = self._format_trend(trend)
        
        prompt = f"""请根据以下数据进行趋势分析和预测说明。

## 分析指标
{metric}

## 历史数据（最近7天）
{historical_str}

## 趋势分析
{trend_str}

## 预测数据（未来7天）
{predictions_str}

## 请输出以下内容：

### 1. 趋势解读
（解读当前趋势方向和强度）

### 2. 预测分析
（说明预测结果和置信度）

### 3. 关键影响因素
（分析可能影响未来表现的因素）

### 4. 行动建议
（基于预测结果的建议）"""
        
        return prompt
    
    def build_qa_prompt(self, question: str, relevant_data: Dict) -> str:
        """
        构建问答 Prompt
        
        Args:
            question: 用户问题
            relevant_data: 相关数据上下文
            
        Returns:
            构建好的 Prompt
        """
        # 格式化数据上下文
        data_context = self._format_data_context(relevant_data)
        
        prompt = f"""用户问题: {question}

## 当前数据概况
{data_context}

请基于以上数据回答用户问题。要求：
1. 回答要简洁、准确
2. 用数据支撑观点
3. 如果数据不足以回答问题，请诚实说明
4. 如有建议，请给出可执行的方案"""
        
        return prompt
    
    def build_suggestion_prompt(self,
                                 store_metrics: List[Dict],
                                 platform_metrics: List[Dict],
                                 issues: List[Dict],
                                 focus_area: str = "all") -> str:
        """
        构建建议 Prompt
        
        Args:
            store_metrics: 门店指标
            platform_metrics: 平台指标
            issues: 问题列表
            focus_area: 关注领域
            
        Returns:
            构建好的 Prompt
        """
        # 格式化门店指标
        stores_str = self._format_metrics_list(store_metrics, "门店指标")
        
        # 格式化平台指标
        platforms_str = self._format_metrics_list(platform_metrics, "平台指标")
        
        # 格式化问题
        issues_str = self._format_issues(issues)
        
        focus_area_desc = {
            'all': '综合分析所有领域',
            'revenue': '重点关注营收相关指标',
            'traffic': '重点关注流量相关指标',
            'conversion': '重点关注转化相关指标',
            'cost': '重点关注成本相关指标'
        }
        
        prompt = f"""请根据以下数据生成经营建议。

## 关注领域
{focus_area_desc.get(focus_area, focus_area)}

{stores_str}

{platforms_str}

## 发现的问题
{issues_str}

## 请输出以下内容：

### 1. 问题优先级排序
（按影响程度排序问题）

### 2. 针对性建议
（每个问题对应的解决方案）

### 3. 预期效果
（实施建议后预期的改善）

### 4. 实施步骤
（具体的执行计划）"""
        
        return prompt
    
    def build_store_comparison_prompt(self, comparison_data: List[Dict],
                                       store_names: List[str]) -> str:
        """
        构建门店对比 Prompt
        
        Args:
            comparison_data: 对比数据
            store_names: 门店名称列表
            
        Returns:
            构建好的 Prompt
        """
        # 格式化对比数据
        comparison_str = self._format_comparison_table(comparison_data)
        
        prompt = f"""请对比分析以下门店的表现。

## 对比门店
{', '.join(store_names)}

## 对比数据
{comparison_str}

## 请输出以下内容：

### 1. 综合对比
（各门店的核心指标对比分析）

### 2. 优势分析
（每个门店的优势在哪里）

### 3. 差距分析
（表现较差门店的问题在哪里）

### 4. 改进建议
（针对每个门店的具体建议）"""
        
        return prompt
    
    def build_trend_analysis_prompt(self, daily_data: List[Dict],
                                     metric: str, trend: Dict) -> str:
        """
        构建趋势分析 Prompt
        
        Args:
            daily_data: 日度数据
            metric: 分析指标
            trend: 趋势信息
            
        Returns:
            构建好的 Prompt
        """
        # 格式化日度数据
        daily_str = self._format_time_series(daily_data, "日度数据", metric)
        
        # 格式化趋势
        trend_str = self._format_trend(trend)
        
        prompt = f"""请分析以下数据的趋势。

## 分析指标
{metric}

{daily_str}

## 趋势统计
{trend_str}

## 请输出以下内容：

### 1. 趋势判断
（当前是上升、下降还是平稳趋势）

### 2. 波动分析
（分析数据波动情况）

### 3. 周期性特征
（是否有周期性规律）

### 4. 异常点分析
（如有异常值，分析可能原因）

### 5. 趋势预测
（对未来走势的预判）"""
        
        return prompt
    
    def build_promotion_eval_prompt(self, before_data: Dict,
                                     during_data: Dict,
                                     after_data: Dict) -> str:
        """
        构建活动评估 Prompt
        
        Args:
            before_data: 活动前数据
            during_data: 活动中数据
            after_data: 活动后数据
            
        Returns:
            构建好的 Prompt
        """
        prompt = f"""请评估以下促销活动的效果。

## 活动前数据（基准）
{json.dumps(before_data, ensure_ascii=False, indent=2)}

## 活动中数据
{json.dumps(during_data, ensure_ascii=False, indent=2)}

## 活动后数据
{json.dumps(after_data, ensure_ascii=False, indent=2)}

## 请输出以下内容：

### 1. 活动效果总结
（活动整体表现如何）

### 2. 核心指标变化
（营收、订单量、客单价等变化）

### 3. ROI 分析
（投入产出比分析）

### 4. 经验总结
（哪些做得好，哪些需要改进）

### 5. 下次活动建议
（对未来活动的建议）"""
        
        return prompt
    
    # ==================== 格式化辅助方法 ====================
    
    def _format_store_ranking(self, data: Dict) -> str:
        """格式化门店排名数据"""
        if not data:
            return "暂无门店排名数据"
        
        # 如果是 DataFrame 转换的数据
        if isinstance(data, dict) and 'stores' in data:
            stores = data['stores']
            lines = []
            for i, store in enumerate(stores[:10], 1):
                name = store.get('brand_store_name', '未知')
                income = store.get('actual_income', 0)
                orders = store.get('valid_order_count', 0)
                lines.append(f"{i}. {name}: 实收 ¥{income:,.0f}, 订单 {orders}")
            return '\n'.join(lines)
        
        # 直接是列表
        if isinstance(data, list):
            lines = []
            for i, store in enumerate(data[:10], 1):
                name = store.get('brand_store_name', '未知')
                income = store.get('actual_income', 0)
                orders = store.get('valid_order_count', 0)
                lines.append(f"{i}. {name}: 实收 ¥{income:,.0f}, 订单 {orders}")
            return '\n'.join(lines)
        
        return str(data)
    
    def _format_platform_comparison(self, data: Dict) -> str:
        """格式化平台对比数据"""
        if not data:
            return "暂无平台对比数据"
        
        # 如果是 DataFrame 转换的数据
        if isinstance(data, dict) and 'platforms' in data:
            platforms = data['platforms']
            lines = []
            for p in platforms:
                name = p.get('platform', '未知')
                income = p.get('actual_income', 0)
                share = p.get('revenue_share', 0)
                orders = p.get('valid_order_count', 0)
                lines.append(f"- {name}: 实收 ¥{income:,.0f} ({share:.1f}%), 订单 {orders}")
            return '\n'.join(lines)
        
        # 直接是列表
        if isinstance(data, list):
            lines = []
            for p in data:
                name = p.get('platform', '未知')
                income = p.get('actual_income', 0)
                share = p.get('revenue_share', 0) if 'revenue_share' in p else 0
                orders = p.get('valid_order_count', 0)
                lines.append(f"- {name}: 实收 ¥{income:,.0f} ({share:.1f}%), 订单 {orders}")
            return '\n'.join(lines)
        
        return str(data)
    
    def _format_anomalies(self, anomalies: List[Dict]) -> str:
        """格式化异常列表"""
        if not anomalies:
            return "✅ 未检测到明显异常"
        
        lines = []
        for anomaly in anomalies:
            anomaly_type = anomaly.get('type', '未知类型')
            store = anomaly.get('store', '未知门店')
            metric = anomaly.get('metric', '未知指标')
            value = anomaly.get('value', 0)
            expected = anomaly.get('expected', 0)
            deviation = anomaly.get('deviation', 0)
            
            direction = "下降" if deviation < 0 else "上升"
            lines.append(f"- ⚠️ [{anomaly_type}] {store} - {metric}: {direction} {abs(deviation):.1f}% (实际: {value:.2f}, 预期: {expected:.2f})")
        
        return '\n'.join(lines)
    
    def _format_summary_stats(self, stats: Dict) -> str:
        """格式化摘要统计"""
        if not stats:
            return ""
        
        lines = ["## 数据摘要"]
        
        if 'date_range' in stats:
            dr = stats['date_range']
            lines.append(f"- 日期范围: {dr.get('start', 'N/A')} 至 {dr.get('end', 'N/A')} ({dr.get('days', 0)} 天)")
        
        if 'stores' in stats:
            lines.append(f"- 门店数量: {stats['stores'].get('count', 0)}")
        
        if 'platforms' in stats:
            platforms = stats['platforms']
            lines.append(f"- 平台数量: {platforms.get('count', 0)} ({', '.join(platforms.get('list', []))})")
        
        if 'revenue' in stats:
            rev = stats['revenue']
            lines.append(f"- 总实收: ¥{rev.get('total', 0):,.0f}")
            lines.append(f"- 平均日收: ¥{rev.get('mean', 0):,.0f}")
        
        if 'orders' in stats:
            orders = stats['orders']
            lines.append(f"- 总订单: {orders.get('total', 0):,}")
        
        lines.append("")
        return '\n'.join(lines)
    
    def _format_time_series(self, data: List[Dict], title: str, metric: str) -> str:
        """格式化时间序列数据"""
        if not data:
            return f"{title}: 暂无数据"
        
        lines = [f"### {title}"]
        for item in data:
            date = item.get('date', '未知')
            value = item.get(metric, 0)
            lines.append(f"- {date}: {value:,.2f}")
        
        return '\n'.join(lines)
    
    def _format_trend(self, trend: Dict) -> str:
        """格式化趋势信息"""
        if not trend:
            return "暂无趋势信息"
        
        direction = trend.get('direction', '未知')
        strength = trend.get('strength', 0)
        daily_change = trend.get('daily_change', 0)
        
        direction_map = {
            'up': '上升',
            'down': '下降',
            'stable': '平稳',
            '上升': '上升',
            '下降': '下降',
            '平稳': '平稳'
        }
        
        lines = [
            f"- 趋势方向: {direction_map.get(direction, direction)}",
            f"- 趋势强度: {strength:.2f}",
            f"- 日均变化: {daily_change:+.2f}"
        ]
        
        return '\n'.join(lines)
    
    def _format_data_context(self, data: Dict) -> str:
        """格式化数据上下文"""
        if not data:
            return "暂无数据"
        
        lines = []
        
        if 'date_range' in data:
            lines.append(f"- 日期范围: {data['date_range']}")
        
        if 'total_income' in data:
            lines.append(f"- 总实收: ¥{data['total_income']:,.0f}")
        
        if 'total_orders' in data:
            lines.append(f"- 总订单: {data['total_orders']:,}")
        
        if 'avg_margin_rate' in data:
            lines.append(f"- 平均到手率: {data['avg_margin_rate']:.1f}%")
        
        if 'store_count' in data:
            lines.append(f"- 门店数: {data['store_count']}")
        
        if 'platforms' in data:
            lines.append(f"- 平台: {', '.join(data['platforms'])}")
        
        return '\n'.join(lines) if lines else str(data)
    
    def _format_metrics_list(self, metrics: List[Dict], title: str) -> str:
        """格式化指标列表"""
        if not metrics:
            return f"## {title}\n暂无数据"
        
        lines = [f"## {title}"]
        for item in metrics:
            lines.append(json.dumps(item, ensure_ascii=False))
        
        return '\n'.join(lines)
    
    def _format_issues(self, issues: List[Dict]) -> str:
        """格式化问题列表"""
        if not issues:
            return "未发现明显问题"
        
        lines = []
        for issue in issues:
            issue_type = issue.get('type', '未知')
            description = issue.get('description', '')
            severity = issue.get('severity', '中')
            lines.append(f"- [{severity}] {issue_type}: {description}")
        
        return '\n'.join(lines)
    
    def _format_comparison_table(self, data: List[Dict]) -> str:
        """格式化对比表格"""
        if not data:
            return "暂无对比数据"
        
        return json.dumps(data, ensure_ascii=False, indent=2)
    
    def truncate_to_context_limit(self, text: str) -> str:
        """
        截断文本以适应上下文长度限制
        
        Args:
            text: 原始文本
            
        Returns:
            截断后的文本
        """
        if len(text) <= self.max_context_length:
            return text
        
        # 截断并添加提示
        truncated = text[:self.max_context_length - 100]
        truncated += "\n\n... [内容已截断以适应长度限制]"
        return truncated


def build_diagnosis_prompt(store_ranking: Dict,
                           platform_comparison: Dict,
                           anomalies: List[Dict],
                           period: str,
                           summary_stats: Dict = None) -> str:
    """
    便捷函数：构建诊断报告 Prompt
    """
    builder = PromptBuilder()
    return builder.build_diagnosis_prompt(
        store_ranking, platform_comparison, anomalies, period, summary_stats
    )


def build_qa_prompt(question: str, relevant_data: Dict) -> str:
    """
    便捷函数：构建问答 Prompt
    """
    builder = PromptBuilder()
    return builder.build_qa_prompt(question, relevant_data)