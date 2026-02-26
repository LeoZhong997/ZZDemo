"""
红线指标检测器
检测外卖运营中的高危信号（商责、回复率、评分、食安等）
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
import logging

from ai.config import get_ai_config

logger = logging.getLogger(__name__)


# 红线规则配置
REDLINE_RULES = {
    'merchant_responsibility': {
        'name': '商责订单',
        'field': 'merchant_cancelled_orders',
        'condition': 'gt',  # greater than
        'threshold': 0,
        'severity': 'high',
        'description': '商责取消订单 > 0',
        'platforms': ['meituan', 'eleme']
    },
    'merchant_cancellation_rate': {
        'name': '商责取消率',
        'field': 'merchant_cancellation_rate',
        'condition': 'gt',
        'threshold': 0.01,  # 1%
        'severity': 'high',
        'description': '商责取消率 > 1%',
        'platforms': ['meituan', 'eleme']
    },
    'reply_rate_5min': {
        'name': '5分钟回复率',
        'field': 'five_min_reply_rate',
        'condition': 'lt',  # less than
        'threshold': 100,
        'consecutive_days': 2,
        'severity': 'medium',
        'description': '5分钟回复率连续2天不合格',
        'platforms': ['meituan']
    },
    'reply_rate_1min': {
        'name': '1分钟回复率',
        'field': 'one_min_reply_rate',
        'condition': 'lt',
        'threshold': 100,
        'consecutive_days': 2,
        'severity': 'medium',
        'description': '1分钟回复率连续2天不合格',
        'platforms': ['meituan']
    },
    'store_score': {
        'name': '店铺评分',
        'field': 'store_score',
        'condition': 'lt',
        'threshold': 4.5,
        'severity': 'medium',
        'description': '店铺评分 < 4.5',
        'platforms': ['meituan']
    },
    'store_score_critical': {
        'name': '店铺评分(严重)',
        'field': 'store_score',
        'condition': 'lt',
        'threshold': 4.0,
        'severity': 'high',
        'description': '店铺评分 < 4.0 (严重)',
        'platforms': ['meituan']
    },
    'store_score_drop': {
        'name': '店铺评分下降',
        'field': 'store_score',
        'condition': 'drop',  # 环比下降
        'threshold': 0.2,
        'severity': 'medium',
        'description': '店铺评分环比下降 > 0.2',
        'platforms': ['meituan']
    },
    'food_safety': {
        'name': '食安负反馈',
        'field': 'food_safety_negative_feedback_rate',
        'condition': 'gt',
        'threshold': 0,
        'severity': 'high',
        'description': '食品安全负反馈率 > 0',
        'platforms': ['meituan']
    },
    'service_negative': {
        'name': '服务负反馈',
        'field': 'service_negative_feedback_score',
        'condition': 'lt',
        'threshold': 4.5,
        'severity': 'medium',
        'description': '服务负反馈得分 < 4.5',
        'platforms': ['meituan']
    },
    'meal_report_rate': {
        'name': '出餐上报率',
        'field': 'meal_completion_report_rate',
        'condition': 'lt',
        'threshold': 95,
        'consecutive_days': 3,
        'severity': 'medium',
        'description': '出餐上报率连续3天 < 95%',
        'platforms': ['meituan']
    },
    'product_satisfaction': {
        'name': '商品满意度',
        'field': 'product_satisfaction',
        'condition': 'lt',
        'threshold': 4.5,
        'severity': 'low',
        'description': '商品满意度 < 4.5',
        'platforms': ['meituan']
    },
    'packaging_satisfaction': {
        'name': '包装满意度',
        'field': 'packaging_satisfaction',
        'condition': 'lt',
        'threshold': 4.5,
        'severity': 'low',
        'description': '包装满意度 < 4.5',
        'platforms': ['meituan']
    }
}

# 严重程度权重
SEVERITY_WEIGHTS = {
    'high': 3,
    'medium': 2,
    'low': 1
}

# 严重程度图标
SEVERITY_ICONS = {
    'high': '🔴',
    'medium': '🟡',
    'low': '🟢'
}


class RedlineDetector:
    """
    红线指标检测器
    
    功能：
    - 检测商责订单
    - 检测回复率问题
    - 检测低评分
    - 检测食安问题
    - 检测服务/商品满意度问题
    - 生成红线汇总报告
    """
    
    def __init__(self, custom_rules: Dict = None):
        """
        初始化红线检测器
        
        Args:
            custom_rules: 自定义规则，会覆盖默认规则
        """
        self.config = get_ai_config('analysis', {})
        self.rules = REDLINE_RULES.copy()
        
        if custom_rules:
            self.rules.update(custom_rules)
    
    def detect_all(self, df: pd.DataFrame,
                   store_col: str = 'brand_store_name',
                   date_col: str = 'date',
                   platform_col: str = 'platform') -> Dict[str, Any]:
        """
        检测所有红线指标
        
        Args:
            df: 原始数据
            store_col: 门店列名
            date_col: 日期列名
            platform_col: 平台列名
            
        Returns:
            {
                'violations': [违规列表],
                'by_store': {门店: [违规]},
                'by_type': {类型: [违规]},
                'summary': {统计摘要},
                'high_risk_stores': [高风险门店列表]
            }
        """
        if df.empty:
            return self._empty_result()
        
        all_violations = []
        
        # 按门店-平台分组检测
        group_cols = [store_col]
        if platform_col in df.columns:
            group_cols.append(platform_col)
        
        for rule_key, rule in self.rules.items():
            field = rule['field']
            
            if field not in df.columns:
                continue
            
            # 特殊处理：评分环比下降使用专门的检测方法
            if rule.get('condition') == 'drop':
                if rule_key == 'store_score_drop':
                    drop_violations = self.detect_store_score_drop(df, store_col, date_col, rule['threshold'])
                    all_violations.extend(drop_violations)
                continue
            
            violations = self._detect_rule(df, rule_key, rule, store_col, date_col, platform_col)
            all_violations.extend(violations)
        
        # 按严重程度排序
        all_violations.sort(key=lambda x: SEVERITY_WEIGHTS.get(x['severity'], 0), reverse=True)
        
        # 汇总统计
        summary = self._generate_summary(all_violations)
        
        # 按门店分组
        by_store = self._group_by_store(all_violations)
        
        # 按类型分组
        by_type = self._group_by_type(all_violations)
        
        # 高风险门店
        high_risk_stores = self._identify_high_risk_stores(by_store)
        
        return {
            'success': True,
            'violations': all_violations,
            'by_store': by_store,
            'by_type': by_type,
            'summary': summary,
            'high_risk_stores': high_risk_stores
        }
    
    def detect_merchant_responsibility(self, df: pd.DataFrame,
                                        store_col: str = 'brand_store_name') -> List[Dict]:
        """
        检测商责订单
        
        Args:
            df: 数据
            store_col: 门店列名
            
        Returns:
            商责违规列表
        """
        if df.empty or 'merchant_cancelled_orders' not in df.columns:
            return []
        
        violations = []
        
        # 按门店聚合
        agg_df = df.groupby(store_col).agg({
            'merchant_cancelled_orders': 'sum',
            'valid_orders': 'sum'
        }).reset_index()
        
        for _, row in agg_df.iterrows():
            if row['merchant_cancelled_orders'] > 0:
                rate = row['merchant_cancelled_orders'] / row['valid_orders'] * 100 if row['valid_orders'] > 0 else 0
                
                violations.append({
                    'type': 'merchant_responsibility',
                    'name': '商责订单',
                    'store': row[store_col],
                    'value': int(row['merchant_cancelled_orders']),
                    'rate': round(rate, 2),
                    'severity': 'high',
                    'description': f"商责取消订单 {int(row['merchant_cancelled_orders'])} 单，商责率 {rate:.2f}%"
                })
        
        return violations
    
    def detect_reply_rate_issues(self, df: pd.DataFrame,
                                  store_col: str = 'brand_store_name',
                                  date_col: str = 'date') -> List[Dict]:
        """
        检测回复率问题
        
        Args:
            df: 数据
            store_col: 门店列名
            date_col: 日期列名
            
        Returns:
            回复率违规列表
        """
        violations = []
        
        for field in ['five_min_reply_rate', 'one_min_reply_rate']:
            if field not in df.columns:
                continue
            
            rule_name = '5分钟回复率' if field == 'five_min_reply_rate' else '1分钟回复率'
            
            # 检测不合格记录
            df_copy = df.copy()
            df_copy['reply_unqualified'] = df_copy[field] < 100
            
            # 按门店统计连续不合格
            for store in df_copy[store_col].unique():
                store_df = df_copy[df_copy[store_col] == store].sort_values(date_col)
                
                # 统计不合格天数
                unqualified_days = store_df[store_df['reply_unqualified']].shape[0]
                
                if unqualified_days > 0:
                    # 检查是否连续
                    consecutive = self._check_consecutive(store_df, 'reply_unqualified', min_days=2)
                    
                    severity = 'high' if consecutive else ('medium' if unqualified_days >= 3 else 'low')
                    
                    violations.append({
                        'type': f'reply_rate_{field}',
                        'name': rule_name,
                        'store': store,
                        'value': f'{unqualified_days}天不合格',
                        'consecutive': consecutive,
                        'severity': severity,
                        'description': f"{rule_name} {unqualified_days} 天不合格{'（连续）' if consecutive else ''}"
                    })
        
        return violations
    
    def detect_low_store_score(self, df: pd.DataFrame,
                                store_col: str = 'brand_store_name') -> List[Dict]:
        """
        检测低评分门店
        
        Args:
            df: 数据
            store_col: 门店列名
            
        Returns:
            低评分违规列表
        """
        if df.empty or 'store_score' not in df.columns:
            return []
        
        violations = []
        
        # 按门店获取最新评分
        agg_df = df.groupby(store_col).agg({
            'store_score': 'mean'
        }).reset_index()
        
        for _, row in agg_df.iterrows():
            score = row['store_score']
            
            if pd.isna(score):
                continue
            
            if score < 4.0:
                violations.append({
                    'type': 'store_score_critical',
                    'name': '店铺评分(严重)',
                    'store': row[store_col],
                    'value': round(score, 2),
                    'severity': 'high',
                    'description': f"店铺评分 {score:.2f}，低于4.0（严重）"
                })
            elif score < 4.5:
                violations.append({
                    'type': 'store_score',
                    'name': '店铺评分',
                    'store': row[store_col],
                    'value': round(score, 2),
                    'severity': 'medium',
                    'description': f"店铺评分 {score:.2f}，低于4.5"
                })
        
        return violations
    
    def detect_store_score_drop(self, df: pd.DataFrame,
                                 store_col: str = 'brand_store_name',
                                 date_col: str = 'date',
                                 threshold: float = 0.2) -> List[Dict]:
        """
        检测店铺评分环比下降
        
        Args:
            df: 数据
            store_col: 门店列名
            date_col: 日期列名
            threshold: 下降阈值（默认0.2）
            
        Returns:
            评分下降违规列表
        """
        if df.empty or 'store_score' not in df.columns:
            return []
        
        violations = []
        
        # 按门店和日期分组，计算每日平均评分
        daily_score = df.groupby([store_col, date_col])['store_score'].mean().reset_index()
        
        for store in daily_score[store_col].unique():
            store_df = daily_score[daily_score[store_col] == store].sort_values(date_col)
            
            if len(store_df) < 2:
                continue
            
            # 计算评分变化
            scores = store_df['store_score'].values
            dates = store_df[date_col].values
            
            for i in range(1, len(scores)):
                if pd.isna(scores[i]) or pd.isna(scores[i-1]):
                    continue
                
                drop = scores[i-1] - scores[i]  # 正值表示下降
                
                if drop > threshold:
                    violations.append({
                        'type': 'store_score_drop',
                        'name': '店铺评分下降',
                        'store': store,
                        'value': round(drop, 2),
                        'previous_score': round(scores[i-1], 2),
                        'current_score': round(scores[i], 2),
                        'date': str(dates[i]),
                        'threshold': threshold,
                        'severity': 'medium',
                        'description': f"店铺评分环比下降 {drop:.2f}（从 {scores[i-1]:.2f} 降至 {scores[i]:.2f}）"
                    })
        
        # 去重，只保留每个门店最大的下降
        if violations:
            store_max_drop = {}
            for v in violations:
                store = v['store']
                if store not in store_max_drop or v['value'] > store_max_drop[store]['value']:
                    store_max_drop[store] = v
            
            violations = list(store_max_drop.values())
        
        return violations
    
    def detect_food_safety_issues(self, df: pd.DataFrame,
                                   store_col: str = 'brand_store_name') -> List[Dict]:
        """
        检测食安问题
        
        Args:
            df: 数据
            store_col: 门店列名
            
        Returns:
            食安违规列表
        """
        if df.empty:
            return []
        
        violations = []
        
        # 检查食安负反馈率
        if 'food_safety_negative_feedback_rate' in df.columns:
            agg_df = df.groupby(store_col).agg({
                'food_safety_negative_feedback_rate': 'max'
            }).reset_index()
            
            for _, row in agg_df.iterrows():
                rate = row['food_safety_negative_feedback_rate']
                
                if pd.notna(rate) and rate > 0:
                    violations.append({
                        'type': 'food_safety',
                        'name': '食安负反馈',
                        'store': row[store_col],
                        'value': f'{rate:.2f}%',
                        'severity': 'high',
                        'description': f"食品安全负反馈率 {rate:.2f}%"
                    })
        
        return violations
    
    def detect_satisfaction_issues(self, df: pd.DataFrame,
                                    store_col: str = 'brand_store_name') -> List[Dict]:
        """
        检测满意度问题
        
        Args:
            df: 数据
            store_col: 门店列名
            
        Returns:
            满意度违规列表
        """
        if df.empty:
            return []
        
        violations = []
        
        # 商品满意度
        if 'product_satisfaction' in df.columns:
            agg_df = df.groupby(store_col)['product_satisfaction'].mean().reset_index()
            
            for _, row in agg_df.iterrows():
                satisfaction = row['product_satisfaction']
                
                if pd.notna(satisfaction) and satisfaction < 90:
                    violations.append({
                        'type': 'product_satisfaction',
                        'name': '商品满意度',
                        'store': row[store_col],
                        'value': f'{satisfaction:.1f}%',
                        'severity': 'low' if satisfaction >= 80 else 'medium',
                        'description': f"商品满意度 {satisfaction:.1f}%"
                    })
        
        # 包装满意度
        if 'packaging_satisfaction' in df.columns:
            agg_df = df.groupby(store_col)['packaging_satisfaction'].mean().reset_index()
            
            for _, row in agg_df.iterrows():
                satisfaction = row['packaging_satisfaction']
                
                if pd.notna(satisfaction) and satisfaction < 90:
                    violations.append({
                        'type': 'packaging_satisfaction',
                        'name': '包装满意度',
                        'store': row[store_col],
                        'value': f'{satisfaction:.1f}%',
                        'severity': 'low' if satisfaction >= 80 else 'medium',
                        'description': f"包装满意度 {satisfaction:.1f}%，可能存在撒漏问题"
                    })
        
        return violations
    
    def get_redline_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        获取红线指标摘要
        
        Args:
            df: 数据
            
        Returns:
            摘要信息
        """
        result = self.detect_all(df)
        
        summary = result['summary']
        summary['high_risk_count'] = len(result['high_risk_stores'])
        summary['total_stores'] = df['brand_store_name'].nunique() if 'brand_store_name' in df.columns else 0
        
        return summary
    
    def get_store_redlines(self, df: pd.DataFrame,
                           store_name: str) -> List[Dict]:
        """
        获取指定门店的红线违规
        
        Args:
            df: 数据
            store_name: 门店名称
            
        Returns:
            该门店的违规列表
        """
        result = self.detect_all(df)
        return result['by_store'].get(store_name, [])
    
    def _detect_rule(self, df: pd.DataFrame,
                     rule_key: str,
                     rule: Dict,
                     store_col: str,
                     date_col: str,
                     platform_col: str) -> List[Dict]:
        """
        检测单条规则
        
        Args:
            df: 数据
            rule_key: 规则键
            rule: 规则配置
            store_col: 门店列名
            date_col: 日期列名
            platform_col: 平台列名
            
        Returns:
            违规列表
        """
        violations = []
        field = rule['field']
        threshold = rule['threshold']
        condition = rule['condition']
        
        # 检查字段是否存在
        if field not in df.columns:
            return violations
        
        # 按门店聚合
        agg_df = df.groupby(store_col).agg({
            field: 'mean' if condition == 'lt' else 'sum'
        }).reset_index()
        
        for _, row in agg_df.iterrows():
            value = row[field]
            store = row[store_col]
            
            if pd.isna(value):
                continue
            
            # 检查条件
            violated = False
            if condition == 'gt' and value > threshold:
                violated = True
            elif condition == 'lt' and value < threshold:
                violated = True
            elif condition == 'eq' and value == threshold:
                violated = True
            
            if violated:
                # 检查连续性（如果需要）
                consecutive = False
                if 'consecutive_days' in rule:
                    consecutive = self._check_consecutive_violation(
                        df, store, field, condition, threshold, rule['consecutive_days'], store_col, date_col
                    )
                
                # 只有在需要连续检测且不连续时跳过
                if 'consecutive_days' in rule and not consecutive:
                    continue
                
                # 生成包含具体数值的描述
                description = self._format_description(rule, value, threshold, condition, consecutive)
                
                # 计算风险分数
                risk_score = SEVERITY_WEIGHTS.get(rule['severity'], 1)
                
                violations.append({
                    'type': rule_key,
                    'name': rule['name'],
                    'store': store,
                    'value': round(value, 2) if isinstance(value, float) else value,
                    'threshold': threshold,
                    'severity': rule['severity'],
                    'consecutive': consecutive,
                    'description': description,
                    'risk_score': risk_score
                })
        
        return violations
    
    def _check_consecutive(self, df: pd.DataFrame, 
                           col: str, 
                           min_days: int = 2) -> bool:
        """
        检查是否存在连续不合格
        
        Args:
            df: 数据（已排序）
            col: 检查列
            min_days: 最小连续天数
            
        Returns:
            是否连续
        """
        if len(df) < min_days:
            return False
        
        consecutive_count = 0
        for val in df[col]:
            if val:
                consecutive_count += 1
                if consecutive_count >= min_days:
                    return True
            else:
                consecutive_count = 0
        
        return False
    
    def _check_consecutive_violation(self, df: pd.DataFrame,
                                      store: str,
                                      field: str,
                                      condition: str,
                                      threshold: float,
                                      min_days: int,
                                      store_col: str,
                                      date_col: str) -> bool:
        """
        检查指定门店是否存在连续违规
        
        Args:
            df: 数据
            store: 门店名称
            field: 字段名
            condition: 条件
            threshold: 阈值
            min_days: 最小连续天数
            store_col: 门店列名
            date_col: 日期列名
            
        Returns:
            是否连续违规
        """
        store_df = df[df[store_col] == store].sort_values(date_col)
        
        if len(store_df) < min_days:
            return False
        
        consecutive_count = 0
        for _, row in store_df.iterrows():
            value = row[field]
            
            if pd.isna(value):
                consecutive_count = 0
                continue
            
            violated = False
            if condition == 'gt' and value > threshold:
                violated = True
            elif condition == 'lt' and value < threshold:
                violated = True
            
            if violated:
                consecutive_count += 1
                if consecutive_count >= min_days:
                    return True
            else:
                consecutive_count = 0
        
        return False
    
    def _generate_summary(self, violations: List[Dict]) -> Dict[str, Any]:
        """生成汇总统计"""
        if not violations:
            return {
                'total': 0,
                'by_severity': {'high': 0, 'medium': 0, 'low': 0},
                'by_type': {},
                'has_high_severity': False
            }
        
        summary = {
            'total': len(violations),
            'by_severity': {'high': 0, 'medium': 0, 'low': 0},
            'by_type': {},
            'has_high_severity': False
        }
        
        for v in violations:
            severity = v.get('severity', 'low')
            summary['by_severity'][severity] = summary['by_severity'].get(severity, 0) + 1
            
            v_type = v.get('type', 'unknown')
            summary['by_type'][v_type] = summary['by_type'].get(v_type, 0) + 1
            
            if severity == 'high':
                summary['has_high_severity'] = True
        
        return summary
    
    def _group_by_store(self, violations: List[Dict]) -> Dict[str, List[Dict]]:
        """按门店分组"""
        by_store = {}
        
        for v in violations:
            store = v.get('store', '未知')
            if store not in by_store:
                by_store[store] = []
            by_store[store].append(v)
        
        # 按严重程度排序每个门店的违规
        for store in by_store:
            by_store[store].sort(
                key=lambda x: SEVERITY_WEIGHTS.get(x['severity'], 0),
                reverse=True
            )
        
        return by_store
    
    def _group_by_type(self, violations: List[Dict]) -> Dict[str, List[Dict]]:
        """按类型分组"""
        by_type = {}
        
        for v in violations:
            v_type = v.get('type', 'unknown')
            if v_type not in by_type:
                by_type[v_type] = []
            by_type[v_type].append(v)
        
        return by_type
    
    def _format_description(self, rule: Dict, value: float, threshold: float, 
                            condition: str, consecutive: bool = False) -> str:
        """
        格式化包含具体数值的描述
        
        Args:
            rule: 规则配置
            value: 实际值
            threshold: 阈值
            condition: 条件 (gt/lt/eq)
            consecutive: 是否连续
            
        Returns:
            格式化的描述字符串
        """
        name = rule['name']
        
        # 根据不同规则类型生成描述
        if condition == 'gt':
            # 大于阈值
            if isinstance(value, float):
                if value < 1:
                    # 百分比类（如 0.01 = 1%）
                    desc = f"{name}: {value*100:.2f}% > {threshold*100:.0f}%"
                else:
                    desc = f"{name}: {value:.2f} > {threshold}"
            else:
                desc = f"{name}: {value} > {threshold}"
        elif condition == 'lt':
            # 小于阈值
            if isinstance(value, float):
                if threshold >= 1:
                    desc = f"{name}: {value:.2f} < {threshold}"
                else:
                    desc = f"{name}: {value:.2f} < {threshold}"
            else:
                desc = f"{name}: {value} < {threshold}"
        else:
            desc = rule['description']
        
        # 添加连续标记
        if consecutive:
            desc += "（连续）"
        
        return desc
    
    def _identify_high_risk_stores(self, by_store: Dict[str, List[Dict]]) -> List[Dict]:
        """识别高风险门店"""
        high_risk = []
        
        for store, violations in by_store.items():
            # 计算风险分数
            risk_score = sum(SEVERITY_WEIGHTS.get(v['severity'], 1) for v in violations)
            
            # 有高严重度违规，或者风险分数 >= 5
            has_high = any(v['severity'] == 'high' for v in violations)
            
            if has_high or risk_score >= 5:
                high_risk.append({
                    'store': store,
                    'risk_score': risk_score,
                    'violation_count': len(violations),
                    'has_high_severity': has_high,
                    'top_issues': [v['name'] for v in violations[:3]]
                })
        
        # 按风险分数排序
        high_risk.sort(key=lambda x: x['risk_score'], reverse=True)
        
        return high_risk
    
    def _empty_result(self) -> Dict[str, Any]:
        """返回空结果"""
        return {
            'success': False,
            'violations': [],
            'by_store': {},
            'by_type': {},
            'summary': {
                'total': 0,
                'by_severity': {'high': 0, 'medium': 0, 'low': 0},
                'by_type': {},
                'has_high_severity': False
            },
            'high_risk_stores': []
        }


def detect_redlines(df: pd.DataFrame, **kwargs) -> Dict[str, Any]:
    """
    便捷函数：检测红线指标
    
    Args:
        df: 数据
        **kwargs: 其他参数
        
    Returns:
        检测结果
    """
    detector = RedlineDetector()
    return detector.detect_all(df, **kwargs)