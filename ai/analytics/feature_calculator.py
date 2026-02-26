"""
特征计算器
提供同比/环比、排名、转化漏斗、综合评分等特征计算功能
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
import logging

from ai.config import get_ai_config

logger = logging.getLogger(__name__)


# 评分权重配置
DEFAULT_SCORE_WEIGHTS = {
    'revenue': 0.35,      # 实收权重
    'orders': 0.25,       # 订单数权重
    'margin_rate': 0.20,  # 到手率权重
    'conversion': 0.20    # 转化率权重
}


class FeatureCalculator:
    """
    特征计算器
    
    功能：
    - 同比/环比计算
    - 排名计算
    - 转化漏斗计算
    - 综合评分
    """
    
    def __init__(self):
        """初始化特征计算器"""
        self.config = get_ai_config('analysis', {})
    
    def calculate_yoy_growth(self, df: pd.DataFrame, 
                              metric: str,
                              date_col: str = 'date',
                              group_col: str = None) -> pd.DataFrame:
        """
        计算同比增长率（与去年同期对比）
        
        Args:
            df: 数据，需包含日期列
            metric: 要计算的指标
            date_col: 日期列名
            group_col: 分组列名（如门店），可选
            
        Returns:
            包含同比增长率的 DataFrame
        """
        if df.empty or metric not in df.columns:
            return pd.DataFrame()
        
        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col])
        
        # 提取年份和周数
        df['year'] = df[date_col].dt.isocalendar().year
        df['week'] = df[date_col].dt.isocalendar().week
        
        # 按年-周聚合
        if group_col and group_col in df.columns:
            agg_df = df.groupby(['year', 'week', group_col])[metric].sum().reset_index()
        else:
            agg_df = df.groupby(['year', 'week'])[metric].sum().reset_index()
        
        # 计算同比
        if len(agg_df['year'].unique()) < 2:
            logger.warning("数据不足一年，无法计算同比")
            return agg_df
        
        # 当年数据
        current_year = agg_df['year'].max()
        current_data = agg_df[agg_df['year'] == current_year].copy()
        
        # 去年数据
        last_year_data = agg_df[agg_df['year'] == current_year - 1].copy()
        
        # 合并计算
        if group_col and group_col in df.columns:
            merge_cols = ['week', group_col]
        else:
            merge_cols = ['week']
        
        merged = current_data.merge(
            last_year_data[merge_cols + [metric]],
            on=merge_cols,
            suffixes=('', '_last_year')
        )
        
        # 计算增长率
        merged['yoy_growth'] = merged.apply(
            lambda row: self._safe_growth_rate(row[metric], row[f'{metric}_last_year']),
            axis=1
        )
        
        return merged
    
    def calculate_wow_growth(self, df: pd.DataFrame,
                              metric: str,
                              date_col: str = 'date',
                              group_col: str = None) -> pd.DataFrame:
        """
        计算环比增长率（与上一周对比）
        
        Args:
            df: 数据
            metric: 要计算的指标
            date_col: 日期列名
            group_col: 分组列名
            
        Returns:
            包含环比增长率的 DataFrame
        """
        if df.empty or metric not in df.columns:
            return pd.DataFrame()
        
        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col])
        
        # 按周聚合
        df['year_week'] = df[date_col].dt.strftime('%Y-W%W')
        
        if group_col and group_col in df.columns:
            agg_df = df.groupby(['year_week', group_col])[metric].sum().reset_index()
        else:
            agg_df = df.groupby(['year_week'])[metric].sum().reset_index()
        
        # 计算环比
        agg_df = agg_df.sort_values('year_week')
        agg_df[f'{metric}_last_week'] = agg_df[metric].shift(1)
        
        agg_df['wow_growth'] = agg_df.apply(
            lambda row: self._safe_growth_rate(row[metric], row[f'{metric}_last_week']),
            axis=1
        )
        
        return agg_df
    
    def calculate_ranking(self, df: pd.DataFrame,
                           metric: str,
                           ascending: bool = False,
                           group_col: str = 'brand_store_name') -> pd.DataFrame:
        """
        计算排名
        
        Args:
            df: 数据
            metric: 排名指标
            ascending: 是否升序（False=从高到低，即排名1是最大的）
            group_col: 分组列名
            
        Returns:
            包含排名的 DataFrame
        """
        if df.empty or metric not in df.columns:
            return pd.DataFrame()
        
        result = df.copy()
        
        # 计算排名
        result['rank'] = result[metric].rank(
            method='min',
            ascending=ascending
        ).astype(int)
        
        # 添加排名变化说明
        result['rank_label'] = result.apply(
            lambda row: f"第{int(row['rank'])}名",
            axis=1
        )
        
        # 添加百分位
        total = len(result)
        result['percentile'] = (1 - (result['rank'] - 1) / total) * 100
        
        return result.sort_values('rank')
    
    def calculate_ranking_change(self, current_df: pd.DataFrame,
                                   previous_df: pd.DataFrame,
                                   metric: str,
                                   group_col: str = 'brand_store_name') -> pd.DataFrame:
        """
        计算排名变化
        
        Args:
            current_df: 当前周期数据
            previous_df: 上一周期数据
            metric: 排名指标
            group_col: 分组列名
            
        Returns:
            包含排名变化的 DataFrame
        """
        if current_df.empty or previous_df.empty:
            return pd.DataFrame()
        
        # 计算两期排名
        current_rank = self.calculate_ranking(current_df, metric, group_col=group_col)
        previous_rank = self.calculate_ranking(previous_df, metric, group_col=group_col)
        
        # 合并
        merged = current_rank[[group_col, 'rank', metric]].merge(
            previous_rank[[group_col, 'rank']].rename(columns={'rank': 'previous_rank'}),
            on=group_col,
            how='left'
        )
        
        # 计算变化（正数表示排名上升）
        merged['rank_change'] = merged['previous_rank'] - merged['rank']
        merged['rank_change_label'] = merged['rank_change'].apply(
            lambda x: f"↑{abs(int(x))}" if x > 0 else (f"↓{abs(int(x))}" if x < 0 else "→")
        )
        
        return merged
    
    def calculate_funnel_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        计算转化漏斗指标
        
        Args:
            df: 数据
            
        Returns:
            漏斗指标字典:
            {
                'exposure_to_entry': 曝光到进店率,
                'entry_to_order': 进店到下单率,
                'overall_conversion': 整体转化率,
                'funnel_data': 各阶段数据
            }
        """
        if df.empty:
            return {"error": "数据为空"}
        
        result = {}
        
        # 汇总各阶段数据
        exposure = df['exposure_count'].sum() if 'exposure_count' in df.columns else 0
        entry = df['entry_count'].sum() if 'entry_count' in df.columns else 0
        orders = df['valid_order_count'].sum() if 'valid_order_count' in df.columns else 0
        
        # 计算转化率
        result['exposure_to_entry'] = (entry / exposure * 100) if exposure > 0 else 0
        result['entry_to_order'] = (orders / entry * 100) if entry > 0 else 0
        result['overall_conversion'] = (orders / exposure * 100) if exposure > 0 else 0
        
        # 漏斗数据
        result['funnel_data'] = {
            'exposure': int(exposure),
            'entry': int(entry),
            'orders': int(orders)
        }
        
        # 漏斗损失
        result['drop_off'] = {
            'exposure_to_entry': int(exposure - entry),
            'entry_to_order': int(entry - orders)
        }
        
        return result
    
    def calculate_store_score(self, store_metrics: Dict[str, float],
                               weights: Dict[str, float] = None) -> float:
        """
        计算门店综合评分 (0-100)
        
        Args:
            store_metrics: 门店指标字典，包含:
                - actual_income: 实收
                - valid_order_count: 订单数
                - margin_rate: 到手率
                - conversion_rate: 转化率
                - avg_order_value: 客单价（可选）
            weights: 自定义权重
            
        Returns:
            综合评分 (0-100)
        """
        if weights is None:
            weights = DEFAULT_SCORE_WEIGHTS
        
        # 提取指标
        revenue = store_metrics.get('actual_income', 0)
        orders = store_metrics.get('valid_order_count', 0)
        margin_rate = store_metrics.get('margin_rate', 0)
        conversion_rate = store_metrics.get('conversion_rate', 0)
        
        # 各维度评分 (0-100)
        # 实收评分：基于阈值
        revenue_score = min(100, revenue / 100000 * 100)  # 假设10万为满分
        
        # 订单评分
        orders_score = min(100, orders / 1000 * 100)  # 假设1000单为满分
        
        # 到手率评分：直接使用比率
        margin_score = min(100, margin_rate)  # 到手率通常在60-80%之间
        
        # 转化率评分
        conversion_score = min(100, conversion_rate * 5)  # 假设20%转化为满分
        
        # 加权平均
        total_score = (
            revenue_score * weights.get('revenue', 0.35) +
            orders_score * weights.get('orders', 0.25) +
            margin_score * weights.get('margin_rate', 0.20) +
            conversion_score * weights.get('conversion', 0.20)
        )
        
        return round(total_score, 2)
    
    def calculate_store_scores_batch(self, df: pd.DataFrame,
                                      weights: Dict[str, float] = None) -> pd.DataFrame:
        """
        批量计算门店综合评分
        
        Args:
            df: 门店聚合数据
            weights: 自定义权重
            
        Returns:
            包含评分的 DataFrame
        """
        if df.empty:
            return pd.DataFrame()
        
        result = df.copy()
        
        # 计算每行的评分
        scores = []
        for _, row in result.iterrows():
            metrics = {
                'actual_income': row.get('actual_income', 0),
                'valid_order_count': row.get('valid_order_count', 0),
                'margin_rate': row.get('margin_rate', 0),
                'conversion_rate': row.get('conversion_rate', 0)
            }
            scores.append(self.calculate_store_score(metrics, weights))
        
        result['score'] = scores
        
        # 添加评级
        result['grade'] = result['score'].apply(self._score_to_grade)
        
        return result.sort_values('score', ascending=False)
    
    def calculate_performance_tier(self, df: pd.DataFrame,
                                    metric: str = 'actual_income') -> pd.DataFrame:
        """
        计算表现分层（A/B/C/D/E 五档）
        
        Args:
            df: 数据
            metric: 分层指标
            
        Returns:
            包含分层的 DataFrame
        """
        if df.empty or metric not in df.columns:
            return pd.DataFrame()
        
        result = df.copy()
        
        # 按分位数分层
        result['tier'] = pd.qcut(
            result[metric].rank(method='first'),
            q=5,
            labels=['E', 'D', 'C', 'B', 'A']
        )
        
        return result
    
    def calculate_comparison_metrics(self, current_df: pd.DataFrame,
                                      previous_df: pd.DataFrame,
                                      metrics: List[str] = None,
                                      group_col: str = 'brand_store_name') -> pd.DataFrame:
        """
        计算对比指标（当前 vs 上一周期）
        
        Args:
            current_df: 当前周期数据
            previous_df: 上一周期数据
            metrics: 对比指标列表
            group_col: 分组列名
            
        Returns:
            包含对比结果的 DataFrame
        """
        if current_df.empty:
            return pd.DataFrame()
        
        if metrics is None:
            metrics = ['actual_income', 'valid_order_count', 'margin_rate', 'conversion_rate']
        
        # 过滤存在的指标
        metrics = [m for m in metrics if m in current_df.columns]
        
        # 聚合
        if group_col and group_col in current_df.columns:
            current_agg = current_df.groupby(group_col)[metrics].sum().reset_index()
            previous_agg = previous_df.groupby(group_col)[metrics].sum().reset_index() if not previous_df.empty else pd.DataFrame()
        else:
            current_agg = current_df[metrics].sum().to_frame().T
            previous_agg = previous_df[metrics].sum().to_frame().T if not previous_df.empty else pd.DataFrame()
        
        if previous_agg.empty:
            result = current_agg.copy()
            for m in metrics:
                result[f'{m}_change'] = 0
                result[f'{m}_growth'] = 0
            return result
        
        # 合并
        merge_cols = [group_col] if group_col and group_col in current_df.columns else []
        result = current_agg.merge(
            previous_agg,
            on=merge_cols,
            suffixes=('', '_prev'),
            how='left'
        )
        
        # 计算变化
        for m in metrics:
            if f'{m}_prev' in result.columns:
                result[f'{m}_change'] = result[m] - result[f'{m}_prev']
                result[f'{m}_growth'] = result.apply(
                    lambda row: self._safe_growth_rate(row[m], row[f'{m}_prev']),
                    axis=1
                )
            else:
                result[f'{m}_change'] = 0
                result[f'{m}_growth'] = 0
        
        return result
    
    def _safe_growth_rate(self, current: float, previous: float) -> float:
        """安全计算增长率"""
        if pd.isna(current) or pd.isna(previous):
            return 0.0
        if previous == 0:
            return 100.0 if current > 0 else (0.0 if current == 0 else -100.0)
        return round(((current - previous) / abs(previous)) * 100, 2)
    
    def _score_to_grade(self, score: float) -> str:
        """分数转评级"""
        if score >= 90:
            return 'A+'
        elif score >= 80:
            return 'A'
        elif score >= 70:
            return 'B+'
        elif score >= 60:
            return 'B'
        elif score >= 50:
            return 'C'
        elif score >= 40:
            return 'D'
        else:
            return 'E'


    def analyze_funnel_breakpoints(self, df: pd.DataFrame,
                                    store_col: str = 'brand_store_name') -> Dict[str, Any]:
        """
        分析流量-转化-复购链条断点
        
        识别：
        - 曝光高但进店少 = 曝光-进店断点（店铺形象/活动问题）
        - 进店高但下单少 = 进店-下单断点（菜单/价格问题）
        - 下单多但实收低 = 活动/毛利问题
        
        Args:
            df: 数据
            store_col: 门店列名
            
        Returns:
            断点分析结果
        """
        if df.empty:
            return {"error": "数据为空"}
        
        results = {}
        
        # 按门店聚合
        agg_rules = {}
        if 'exposure_count' in df.columns:
            agg_rules['exposure_count'] = 'sum'
        if 'entry_count' in df.columns:
            agg_rules['entry_count'] = 'sum'
        if 'valid_orders' in df.columns:
            agg_rules['valid_orders'] = 'sum'
        if 'actual_income' in df.columns:
            agg_rules['actual_income'] = 'sum'
        if 'turnover' in df.columns:
            agg_rules['turnover'] = 'sum'
        
        if not agg_rules:
            return {"error": "缺少必要字段"}
        
        agg_df = df.groupby(store_col).agg(agg_rules).reset_index()
        
        for _, row in agg_df.iterrows():
            store = row[store_col]
            
            store_result = {
                'breakpoints': [],
                'has_breakpoint': False,
                'primary_issue': None
            }
            
            exposure = row.get('exposure_count', 0)
            entry = row.get('entry_count', 0)
            orders = row.get('valid_orders', 0)
            income = row.get('actual_income', 0)
            turnover = row.get('turnover', 0)
            
            # 计算各阶段转化率
            exposure_to_entry = (entry / exposure * 100) if exposure > 0 else 0
            entry_to_order = (orders / entry * 100) if entry > 0 else 0
            margin_rate = (income / turnover * 100) if turnover > 0 else 0
            
            store_result['metrics'] = {
                'exposure': int(exposure),
                'entry': int(entry),
                'orders': int(orders),
                'income': float(income),
                'exposure_to_entry_rate': round(exposure_to_entry, 2),
                'entry_to_order_rate': round(entry_to_order, 2),
                'margin_rate': round(margin_rate, 2)
            }
            
            # 检测断点
            
            # 1. 曝光-进店断点（转化率低于10%）
            if exposure > 100 and exposure_to_entry < 10:
                store_result['breakpoints'].append({
                    'stage': 'exposure_to_entry',
                    'issue': '曝光-进店断点',
                    'description': f"曝光{exposure:,}次但进店仅{entry:,}次，转化率{exposure_to_entry:.1f}%",
                    'possible_reasons': ['店铺头图不吸引', '店铺名称不明确', '活动力度不够', '评分低影响点击'],
                    'severity': 'high' if exposure_to_entry < 5 else 'medium'
                })
                store_result['has_breakpoint'] = True
            
            # 2. 进店-下单断点（转化率低于15%）
            if entry > 50 and entry_to_order < 15:
                store_result['breakpoints'].append({
                    'stage': 'entry_to_order',
                    'issue': '进店-下单断点',
                    'description': f"进店{entry:,}次但下单仅{orders:,}次，转化率{entry_to_order:.1f}%",
                    'possible_reasons': ['菜单结构混乱', '价格不具竞争力', '起送价/配送费过高', '缺少爆款'],
                    'severity': 'high' if entry_to_order < 10 else 'medium'
                })
                store_result['has_breakpoint'] = True
            
            # 3. 下单-实收断点（到手率低于55%）
            if orders > 0 and margin_rate < 55:
                store_result['breakpoints'].append({
                    'stage': 'order_to_income',
                    'issue': '下单-实收断点（毛利问题）',
                    'description': f"到手率仅{margin_rate:.1f}%，活动力度过大或成本过高",
                    'possible_reasons': ['满减活动力度过大', '推广花费过高', '平台佣金增加', '食材成本上升'],
                    'severity': 'high' if margin_rate < 50 else 'medium'
                })
                store_result['has_breakpoint'] = True
            
            # 确定主要问题
            if store_result['breakpoints']:
                store_result['breakpoints'].sort(key=lambda x: 0 if x['severity'] == 'high' else 1)
                store_result['primary_issue'] = store_result['breakpoints'][0]['issue']
            
            results[store] = store_result
        
        # 汇总统计
        total_stores = len(results)
        stores_with_breakpoints = sum(1 for r in results.values() if r['has_breakpoint'])
        
        summary = {
            'total_stores': total_stores,
            'stores_with_breakpoints': stores_with_breakpoints,
            'breakpoint_rate': round(stores_with_breakpoints / total_stores * 100, 1) if total_stores > 0 else 0,
            'by_breakpoint_type': {}
        }
        
        # 按断点类型统计
        for store_result in results.values():
            for bp in store_result['breakpoints']:
                bp_type = bp['stage']
                summary['by_breakpoint_type'][bp_type] = summary['by_breakpoint_type'].get(bp_type, 0) + 1
        
        return {
            'success': True,
            'summary': summary,
            'by_store': results
        }
    
    def calculate_revenue_profit_gap(self, df: pd.DataFrame,
                                      store_col: str = 'brand_store_name',
                                      date_col: str = 'date') -> Dict[str, Any]:
        """
        计算收入与利润差距
        
        分析：
        - 营业额增长 vs 实收增长
        - 识别增收不增利的情况
        
        Args:
            df: 数据
            store_col: 门店列名
            date_col: 日期列名
            
        Returns:
            收入利润差距分析
        """
        if df.empty or date_col not in df.columns:
            return {"error": "数据为空或缺少日期列"}
        
        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col])
        
        # 分割时间段
        min_date = df[date_col].min()
        max_date = df[date_col].max()
        mid_date = min_date + (max_date - min_date) / 2
        
        first_half = df[df[date_col] <= mid_date]
        second_half = df[df[date_col] > mid_date]
        
        results = {}
        
        for store in df[store_col].unique():
            first_store = first_half[first_half[store_col] == store]
            second_store = second_half[second_half[store_col] == store]
            
            if first_store.empty or second_store.empty:
                continue
            
            # 营业额变化
            first_turnover = first_store['turnover'].sum() if 'turnover' in first_store.columns else 0
            second_turnover = second_store['turnover'].sum() if 'turnover' in second_store.columns else 0
            
            # 实收变化
            first_income = first_store['actual_income'].sum() if 'actual_income' in first_store.columns else 0
            second_income = second_store['actual_income'].sum() if 'actual_income' in second_store.columns else 0
            
            # 订单变化
            first_orders = first_store['valid_orders'].sum() if 'valid_orders' in first_store.columns else 0
            second_orders = second_store['valid_orders'].sum() if 'valid_orders' in second_store.columns else 0
            
            # 计算变化率
            turnover_change = ((second_turnover - first_turnover) / first_turnover * 100) if first_turnover > 0 else 0
            income_change = ((second_income - first_income) / first_income * 100) if first_income > 0 else 0
            orders_change = ((second_orders - first_orders) / first_orders * 100) if first_orders > 0 else 0
            
            # 到手率变化
            first_margin = (first_income / first_turnover * 100) if first_turnover > 0 else 0
            second_margin = (second_income / second_turnover * 100) if second_turnover > 0 else 0
            margin_change = second_margin - first_margin
            
            # 客单价变化
            first_aov = (first_income / first_orders) if first_orders > 0 else 0
            second_aov = (second_income / second_orders) if second_orders > 0 else 0
            aov_change = ((second_aov - first_aov) / first_aov * 100) if first_aov > 0 else 0
            
            store_result = {
                'first_period': {
                    'turnover': round(first_turnover, 2),
                    'income': round(first_income, 2),
                    'orders': int(first_orders),
                    'margin_rate': round(first_margin, 2),
                    'avg_order_value': round(first_aov, 2)
                },
                'second_period': {
                    'turnover': round(second_turnover, 2),
                    'income': round(second_income, 2),
                    'orders': int(second_orders),
                    'margin_rate': round(second_margin, 2),
                    'avg_order_value': round(second_aov, 2)
                },
                'changes': {
                    'turnover_change': round(turnover_change, 2),
                    'income_change': round(income_change, 2),
                    'orders_change': round(orders_change, 2),
                    'margin_change': round(margin_change, 2),
                    'aov_change': round(aov_change, 2)
                }
            }
            
            # 判断增收不增利
            if turnover_change > 0 and income_change <= 0:
                store_result['status'] = 'revenue_up_profit_down'
                store_result['alert'] = f"营业额增长{turnover_change:.1f}%但实收下降{abs(income_change):.1f}%，活动力度过大"
            elif turnover_change > 0 and margin_change < -3:
                store_result['status'] = 'margin_declining'
                store_result['alert'] = f"营业额增长但到手率下降{abs(margin_change):.1f}%，需优化活动结构"
            elif income_change > turnover_change:
                store_result['status'] = 'healthy'
                store_result['alert'] = "实收增速高于营业额增速，经营效率提升"
            else:
                store_result['status'] = 'normal'
                store_result['alert'] = None
            
            results[store] = store_result
        
        return {
            'success': True,
            'period': {
                'first': f"{min_date.date()} 至 {mid_date.date()}",
                'second': f"{mid_date.date()} 至 {max_date.date()}"
            },
            'by_store': results
        }


def calculate_features(df: pd.DataFrame, feature_type: str = 'all', **kwargs) -> Any:
    """
    便捷函数：计算特征
    
    Args:
        df: 数据
        feature_type: 特征类型 (ranking/funnel/score/comparison/breakpoints/revenue_gap/all)
        **kwargs: 其他参数
        
    Returns:
        计算结果
    """
    calculator = FeatureCalculator()
    
    if feature_type == 'ranking':
        metric = kwargs.get('metric', 'actual_income')
        return calculator.calculate_ranking(df, metric)
    elif feature_type == 'funnel':
        return calculator.calculate_funnel_metrics(df)
    elif feature_type == 'score':
        return calculator.calculate_store_scores_batch(df)
    elif feature_type == 'comparison':
        previous_df = kwargs.get('previous_df', pd.DataFrame())
        return calculator.calculate_comparison_metrics(df, previous_df)
    elif feature_type == 'breakpoints':
        return calculator.analyze_funnel_breakpoints(df)
    elif feature_type == 'revenue_gap':
        return calculator.calculate_revenue_profit_gap(df)
    elif feature_type == 'all':
        # 返回所有特征
        return {
            'ranking': calculator.calculate_ranking(df, 'actual_income'),
            'funnel': calculator.calculate_funnel_metrics(df),
            'scores': calculator.calculate_store_scores_batch(df),
            'breakpoints': calculator.analyze_funnel_breakpoints(df)
        }
    else:
        raise ValueError(f"不支持的特征类型: {feature_type}")
