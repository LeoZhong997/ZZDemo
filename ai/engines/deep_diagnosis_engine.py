"""
深度诊断引擎
整合红线检测、健康度分析、断点分析，生成完整的深度诊断报告
"""
import pandas as pd
from typing import Dict, Any, List, Optional
import logging

from ai.config import get_ai_config
from ai.core.llm_adapter import get_llm_adapter
from ai.analytics.redline_detector import RedlineDetector, detect_redlines
from ai.analytics.health_analyzer import HealthAnalyzer, analyze_store_health
from ai.analytics.feature_calculator import FeatureCalculator
from ai.analytics.data_aggregator import DataAggregator
from ai.prompts.deep_diagnosis_prompts import (
    build_deep_diagnosis_prompt,
    DEEP_DIAGNOSIS_SYSTEM_PROMPT
)
from ai.events.event_manager import get_event_manager

logger = logging.getLogger(__name__)


class DeepDiagnosisEngine:
    """
    深度诊断引擎
    
    功能：
    - 整合多维度数据分析
    - 生成门店诊断表
    - 识别共性风险
    - 生成 SMART 行动清单
    - 调用 LLM 生成深度分析报告
    """
    
    def __init__(self, llm_adapter=None):
        """
        初始化深度诊断引擎
        
        Args:
            llm_adapter: LLM适配器实例，None则自动获取
        """
        self.config = get_ai_config('analysis', {})
        self.llm_adapter = llm_adapter
        
        # 初始化各分析器
        self.redline_detector = RedlineDetector()
        self.health_analyzer = HealthAnalyzer()
        self.feature_calculator = FeatureCalculator()
        self.data_aggregator = DataAggregator()
    
    def generate_deep_diagnosis(self,
                                 df: pd.DataFrame,
                                 period: str = "本周",
                                 events: List[Dict] = None,
                                 use_llm: bool = True) -> Dict[str, Any]:
        """
        生成深度诊断报告
        
        Args:
            df: 原始数据
            period: 报告周期描述
            events: 特殊事件列表
            use_llm: 是否调用LLM生成分析
            
        Returns:
            完整诊断报告
        """
        if df.empty:
            return {
                'success': False,
                'error': '数据为空，无法生成诊断报告'
            }
        
        # 1. 数据摘要
        summary_stats = self._generate_summary_stats(df)
        
        # 2. 健康度分析
        health_data = self.health_analyzer.generate_all_stores_report(df)
        
        # 3. 红线检测
        redline_data = self.redline_detector.detect_all(df)
        
        # 4. 断点分析
        breakpoint_data = self.feature_calculator.analyze_funnel_breakpoints(df)
        
        # 5. 收入利润差距分析
        revenue_gap_data = self.feature_calculator.calculate_revenue_profit_gap(df)
        
        # 6. 获取事件
        if events is None:
            event_manager = get_event_manager()
            date_range = summary_stats.get('date_range', {})
            start_date = date_range.get('start', '')
            end_date = date_range.get('end', '')
            store_names = df['brand_store_name'].unique().tolist() if 'brand_store_name' in df.columns else []
            events = event_manager.get_events_for_diagnosis(start_date, end_date, store_names)
        
        # 7. 生成建议
        recommendations = self._generate_recommendations(health_data, redline_data, breakpoint_data)
        
        # 构建基础报告
        report = {
            'success': True,
            'period': period,
            'summary_stats': summary_stats,
            'health_data': health_data,
            'redline_data': redline_data,
            'breakpoint_data': breakpoint_data,
            'revenue_gap_data': revenue_gap_data,
            'events': events,
            'recommendations': recommendations,
            'llm_analysis': None
        }
        
        # 8. 调用LLM生成深度分析
        if use_llm:
            try:
                llm_analysis = self._generate_llm_analysis(
                    period, summary_stats, health_data, redline_data,
                    breakpoint_data, events, recommendations
                )
                report['llm_analysis'] = llm_analysis
            except Exception as e:
                logger.error(f"LLM分析失败: {e}")
                report['llm_error'] = str(e)
        
        return report
    
    def generate_store_diagnosis_table(self, df: pd.DataFrame) -> List[Dict]:
        """
        生成门店诊断表
        
        Args:
            df: 数据
            
        Returns:
            门店诊断列表
        """
        if df.empty:
            return []
        
        # 健康度分析
        health_df = self.health_analyzer.calculate_health_score(df)
        
        # 红线检测
        redline_data = self.redline_detector.detect_all(df)
        
        # 断点分析
        breakpoint_data = self.feature_calculator.analyze_funnel_breakpoints(df)
        
        diagnosis_table = []
        
        for _, row in health_df.iterrows():
            store_name = row['brand_store_name']
            health_score = row['health_score']
            traffic_light = row['traffic_light']
            
            # 获取红线违规
            violations = redline_data['by_store'].get(store_name, [])
            
            # 获取断点
            store_breakpoints = breakpoint_data['by_store'].get(store_name, {})
            breakpoints = store_breakpoints.get('breakpoints', [])
            
            # 核心问题
            issues = []
            for v in violations[:3]:
                issues.append({
                    'type': v['type'],
                    'name': v['name'],
                    'severity': v['severity'],
                    'description': v.get('description', '')
                })
            
            for bp in breakpoints[:2]:
                issues.append({
                    'type': 'breakpoint',
                    'name': bp['issue'],
                    'severity': bp['severity'],
                    'description': bp['description']
                })
            
            diagnosis_table.append({
                'store_name': store_name,
                'platform': '美团',  # 可以后续细化
                'health_score': round(health_score, 2),
                'traffic_light': traffic_light,
                'status_label': self._get_status_label(traffic_light),
                'issues': issues,
                'dimension_scores': {
                    'revenue': round(row.get('revenue_score', 0), 2),
                    'compliance': round(row.get('compliance_score', 0), 2),
                    'reputation': round(row.get('reputation_score', 0), 2),
                    'efficiency': round(row.get('efficiency_score', 0), 2)
                },
                'risk_level': '高' if traffic_light == '🔴' else ('中' if traffic_light == '🟡' else '低')
            })
        
        # 按健康度排序
        diagnosis_table.sort(key=lambda x: x['health_score'])
        
        return diagnosis_table
    
    def analyze_common_risks(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        分析共性风险
        
        Args:
            df: 数据
            
        Returns:
            共性风险分析
        """
        redline_data = self.redline_detector.detect_all(df)
        breakpoint_data = self.feature_calculator.analyze_funnel_breakpoints(df)
        
        common_risks = []
        
        # 从红线数据分析共性风险
        by_type = redline_data.get('by_type', {})
        
        type_names = {
            'merchant_responsibility': '商责订单',
            'merchant_cancellation_rate': '商责取消率',
            'reply_rate_5min': '5分钟回复率',
            'store_score': '店铺评分',
            'food_safety': '食安负反馈',
            'product_satisfaction': '商品满意度',
            'packaging_satisfaction': '包装满意度'
        }
        
        for v_type, violations in by_type.items():
            if len(violations) >= 2:  # 至少2家店有同样问题
                stores = [v['store'] for v in violations]
                common_risks.append({
                    'type': v_type,
                    'name': type_names.get(v_type, v_type),
                    'affected_count': len(violations),
                    'affected_stores': stores,
                    'severity': violations[0].get('severity', 'medium'),
                    'suggestion': self._get_risk_suggestion(v_type)
                })
        
        # 从断点数据分析共性风险
        bp_summary = breakpoint_data.get('summary', {})
        by_breakpoint_type = bp_summary.get('by_breakpoint_type', {})
        
        bp_names = {
            'exposure_to_entry': '曝光-进店断点',
            'entry_to_order': '进店-下单断点',
            'order_to_income': '下单-实收断点（毛利问题）'
        }
        
        for bp_type, count in by_breakpoint_type.items():
            if count >= 2:
                common_risks.append({
                    'type': f'breakpoint_{bp_type}',
                    'name': bp_names.get(bp_type, bp_type),
                    'affected_count': count,
                    'severity': 'medium',
                    'suggestion': self._get_breakpoint_suggestion(bp_type)
                })
        
        # 按影响数量排序
        common_risks.sort(key=lambda x: x['affected_count'], reverse=True)
        
        return {
            'success': True,
            'common_risks': common_risks,
            'total_risk_types': len(common_risks)
        }
    
    def generate_action_plan(self, df: pd.DataFrame,
                              focus_stores: List[str] = None) -> List[Dict]:
        """
        生成行动清单
        
        Args:
            df: 数据
            focus_stores: 重点关注的门店
            
        Returns:
            行动清单
        """
        actions = []
        
        # 红线数据
        redline_data = self.redline_detector.detect_all(df)
        
        # 健康度数据
        health_df = self.health_analyzer.calculate_health_score(df)
        
        # 高风险门店
        high_risk_stores = redline_data.get('high_risk_stores', [])
        
        # 按门店生成行动
        processed_stores = set()
        
        for store in high_risk_stores:
            store_name = store['store']
            
            if focus_stores and store_name not in focus_stores:
                continue
            
            if store_name in processed_stores:
                continue
            
            processed_stores.add(store_name)
            
            violations = redline_data['by_store'].get(store_name, [])
            
            for v in violations[:2]:  # 每个门店最多2条行动
                priority = 'P0' if v['severity'] == 'high' else ('P1' if v['severity'] == 'medium' else 'P2')
                
                actions.append({
                    'priority': priority,
                    'stores': store_name,
                    'issue': v['name'],
                    'action': self._get_action_for_issue(v['type']),
                    'how': self._get_execution_standard(v['type']),
                    'expected_result': self._get_expected_result(v['type'])
                })
        
        # 添加全局行动（针对共性风险）
        common_risks = self.analyze_common_risks(df)
        
        for risk in common_risks.get('common_risks', [])[:3]:
            actions.append({
                'priority': 'P1',
                'stores': f"涉及{risk['affected_count']}家店",
                'issue': risk['name'],
                'action': risk['suggestion'],
                'how': '统一培训/调整',
                'expected_result': '风险消除'
            })
        
        # 按优先级排序
        actions.sort(key=lambda x: x['priority'])
        
        return actions[:10]  # 最多10条
    
    def _generate_summary_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """生成数据摘要"""
        stats = {}
        
        # 日期范围
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            stats['date_range'] = {
                'start': df['date'].min().strftime('%Y-%m-%d'),
                'end': df['date'].max().strftime('%Y-%m-%d'),
                'days': (df['date'].max() - df['date'].min()).days + 1
            }
        
        # 门店
        if 'brand_store_name' in df.columns:
            stats['stores'] = {
                'count': df['brand_store_name'].nunique(),
                'list': df['brand_store_name'].unique().tolist()
            }
        
        # 平台
        if 'platform' in df.columns:
            stats['platforms'] = {
                'list': df['platform'].unique().tolist()
            }
        else:
            stats['platforms'] = {'list': ['美团']}
        
        # 营收
        if 'actual_income' in df.columns:
            stats['revenue'] = {
                'total': float(df['actual_income'].sum()),
                'mean': float(df['actual_income'].mean()),
                'max': float(df['actual_income'].max()),
                'min': float(df['actual_income'].min())
            }
        
        # 订单
        if 'valid_orders' in df.columns:
            stats['orders'] = {
                'total': int(df['valid_orders'].sum())
            }
        elif 'valid_order_count' in df.columns:
            stats['orders'] = {
                'total': int(df['valid_order_count'].sum())
            }
        
        return stats
    
    def _generate_recommendations(self,
                                   health_data: Dict,
                                   redline_data: Dict,
                                   breakpoint_data: Dict) -> List[Dict]:
        """生成建议"""
        recommendations = []
        
        # 基于红线违规
        high_risk = redline_data.get('high_risk_stores', [])
        for store in high_risk[:3]:
            for issue in store.get('top_issues', [])[:2]:
                recommendations.append({
                    'priority': 'P0',
                    'stores': store['store'],
                    'issue': issue,
                    'action': '立即处理',
                    'expected_result': '风险消除'
                })
        
        # 基于断点
        bp_summary = breakpoint_data.get('summary', {})
        if bp_summary.get('stores_with_breakpoints', 0) > 0:
            recommendations.append({
                'priority': 'P1',
                'stores': f"{bp_summary['stores_with_breakpoints']}家门店",
                'issue': '转化漏斗断点',
                'action': '分析并优化转化环节',
                'expected_result': '转化率提升'
            })
        
        return recommendations[:5]
    
    def _generate_llm_analysis(self,
                                period: str,
                                summary_stats: Dict,
                                health_data: Dict,
                                redline_data: Dict,
                                breakpoint_data: Dict,
                                events: List[Dict],
                                recommendations: List[Dict]) -> str:
        """调用LLM生成深度分析"""
        # 获取LLM适配器
        if self.llm_adapter is None:
            self.llm_adapter = get_llm_adapter()
        
        # 构建Prompt
        prompt = build_deep_diagnosis_prompt(
            period=period,
            summary_stats=summary_stats,
            health_data=health_data,
            redline_data=redline_data,
            breakpoint_data=breakpoint_data,
            events=events,
            recommendations=recommendations
        )
        
        # 调用LLM
        messages = [
            {"role": "system", "content": DEEP_DIAGNOSIS_SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]
        
        response = self.llm_adapter.chat(messages)
        
        return response
    
    def _get_status_label(self, traffic_light: str) -> str:
        """获取状态标签"""
        labels = {
            '🟢': '健康',
            '🟡': '需关注',
            '🔴': '高危'
        }
        return labels.get(traffic_light, '未知')
    
    def _get_risk_suggestion(self, risk_type: str) -> str:
        """获取风险建议"""
        suggestions = {
            'merchant_responsibility': '禁止商家端直接取消，加强出餐流程管理',
            'merchant_cancellation_rate': '优化出餐流程，确保按时完成',
            'reply_rate_5min': '调整排班，确保高峰期及时响应',
            'store_score': '分析差评原因，针对性改进',
            'food_safety': '立即排查食安隐患，加强操作规范',
            'product_satisfaction': '优化菜品口味，收集反馈改进',
            'packaging_satisfaction': '更换包装材料，防止撒漏'
        }
        return suggestions.get(risk_type, '请人工分析并制定改进方案')
    
    def _get_breakpoint_suggestion(self, bp_type: str) -> str:
        """获取断点建议"""
        suggestions = {
            'exposure_to_entry': '优化店铺头图、活动力度，提升点击率',
            'entry_to_order': '优化菜单结构、价格策略，提升转化率',
            'order_to_income': '优化活动结构，控制成本，提升到手率'
        }
        return suggestions.get(bp_type, '分析具体原因并优化')
    
    def _get_action_for_issue(self, issue_type: str) -> str:
        """获取针对问题的行动"""
        actions = {
            'merchant_responsibility': '禁止商家端直接取消，必须电话沟通后由顾客取消或申诉',
            'merchant_cancellation_rate': '优化出餐流程，确保按时完成；加强员工培训',
            'reply_rate_5min': '调整排班，确保高峰期1分钟内响应；设置自动回复',
            'store_score': '分析差评原因，针对性改进菜品口味/包装/服务',
            'food_safety': '立即排查食安隐患，加强食材管理和操作规范',
            'product_satisfaction': '优化菜品口味，收集顾客反馈并改进',
            'packaging_satisfaction': '更换包装材料，加强封口防止撒漏'
        }
        return actions.get(issue_type, '请人工分析具体原因并制定改进方案')
    
    def _get_execution_standard(self, issue_type: str) -> str:
        """获取执行标准"""
        standards = {
            'merchant_responsibility': '所有取消必须先电话沟通，记录在案',
            'merchant_cancellation_rate': '出餐超时预警机制，提前10分钟提醒',
            'reply_rate_5min': '高峰期专人负责回复，设置提醒闹钟',
            'store_score': '每日分析差评，制定针对性改进措施',
            'food_safety': '每日检查食材，严格执行操作规范',
            'product_satisfaction': '每周收集反馈，持续优化',
            'packaging_satisfaction': '测试新包装，确保无撒漏'
        }
        return standards.get(issue_type, '按标准流程执行')
    
    def _get_expected_result(self, issue_type: str) -> str:
        """获取预期结果"""
        results = {
            'merchant_responsibility': '商责降为0',
            'merchant_cancellation_rate': '商责取消率降至1%以下',
            'reply_rate_5min': '回复率达到100%',
            'store_score': '评分提升至4.5以上',
            'food_safety': '食安负反馈降为0',
            'product_satisfaction': '商品满意度提升至90%以上',
            'packaging_satisfaction': '包装满意度提升至90%以上'
        }
        return results.get(issue_type, '问题得到改善')


def generate_deep_diagnosis(df: pd.DataFrame, **kwargs) -> Dict[str, Any]:
    """
    便捷函数：生成深度诊断报告
    
    Args:
        df: 数据
        **kwargs: 其他参数
        
    Returns:
        诊断报告
    """
    engine = DeepDiagnosisEngine()
    return engine.generate_deep_diagnosis(df, **kwargs)