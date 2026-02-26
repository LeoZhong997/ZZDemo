"""
门店健康度分析器
提供综合健康度评分、红/黄/绿灯评级、财务健康度分析等功能
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
import logging

from ai.config import get_ai_config
from ai.analytics.redline_detector import RedlineDetector, SEVERITY_WEIGHTS

logger = logging.getLogger(__name__)


# 健康度评分权重配置
HEALTH_SCORE_WEIGHTS = {
    'revenue': 0.25,           # 营收健康度
    'compliance': 0.25,        # 合规性（商责、回复率等）
    'reputation': 0.25,        # 口碑（评分、满意度）
    'efficiency': 0.25         # 效率（到手率、转化率）
}

# 信号灯阈值
TRAFFIC_LIGHT_THRESHOLDS = {
    'green': 80,    # >= 80 分为绿灯
    'yellow': 60,   # >= 60 且 < 80 为黄灯
    'red': 0        # < 60 为红灯
}

# 行业基准值
INDUSTRY_BENCHMARKS = {
    'margin_rate': 55.0,        # 到手率基准 55%
    'conversion_rate': 15.0,    # 转化率基准 15%
    'store_score': 4.5,         # 评分基准 4.5
    'reply_rate': 100.0         # 回复率基准 100%
}


class HealthAnalyzer:
    """
    门店健康度分析器
    
    功能：
    - 计算综合健康度评分 (0-100)
    - 生成红/黄/绿灯评级
    - 分析财务健康度（增收不增利检测）
    - 分析运营合规性
    - 分析口碑与质量
    - 生成完整健康报告
    """
    
    def __init__(self, weights: Dict[str, float] = None):
        """
        初始化健康度分析器
        
        Args:
            weights: 自定义评分权重
        """
        self.config = get_ai_config('analysis', {})
        self.weights = weights or HEALTH_SCORE_WEIGHTS.copy()
        self.redline_detector = RedlineDetector()
    
    def calculate_health_score(self, df: pd.DataFrame,
                                store_col: str = 'brand_store_name') -> pd.DataFrame:
        """
        计算门店综合健康度评分
        
        Args:
            df: 原始数据
            store_col: 门店列名
            
        Returns:
            包含健康度评分的 DataFrame
        """
        if df.empty:
            return pd.DataFrame()
        
        # 按门店聚合核心指标
        agg_rules = {}
        
        # 营收指标
        if 'actual_income' in df.columns:
            agg_rules['actual_income'] = 'sum'
        if 'valid_orders' in df.columns:
            agg_rules['valid_orders'] = 'sum'
        
        # 合规指标
        if 'merchant_cancelled_orders' in df.columns:
            agg_rules['merchant_cancelled_orders'] = 'sum'
        if 'five_min_reply_rate' in df.columns:
            agg_rules['five_min_reply_rate'] = 'mean'
        
        # 口碑指标
        if 'store_score' in df.columns:
            agg_rules['store_score'] = 'mean'
        if 'product_satisfaction' in df.columns:
            agg_rules['product_satisfaction'] = 'mean'
        if 'packaging_satisfaction' in df.columns:
            agg_rules['packaging_satisfaction'] = 'mean'
        
        # 效率指标
        if 'net_margin_rate' in df.columns:
            agg_rules['net_margin_rate'] = 'mean'
        elif 'actual_income' in df.columns and 'turnover' in df.columns:
            # 后面会计算
            pass
        
        if 'order_conversion_rate' in df.columns:
            agg_rules['order_conversion_rate'] = 'mean'
        if 'store_entry_rate' in df.columns:
            agg_rules['store_entry_rate'] = 'mean'
        
        # 执行聚合
        if agg_rules:
            store_df = df.groupby(store_col).agg(agg_rules).reset_index()
        else:
            return pd.DataFrame()
        
        # 计算各维度评分
        store_df['revenue_score'] = store_df.apply(
            lambda row: self._calculate_revenue_score(row), axis=1
        )
        
        store_df['compliance_score'] = store_df.apply(
            lambda row: self._calculate_compliance_score(row, df, row[store_col], store_col), axis=1
        )
        
        store_df['reputation_score'] = store_df.apply(
            lambda row: self._calculate_reputation_score(row), axis=1
        )
        
        store_df['efficiency_score'] = store_df.apply(
            lambda row: self._calculate_efficiency_score(row), axis=1
        )
        
        # 计算综合评分
        store_df['health_score'] = (
            store_df['revenue_score'] * self.weights['revenue'] +
            store_df['compliance_score'] * self.weights['compliance'] +
            store_df['reputation_score'] * self.weights['reputation'] +
            store_df['efficiency_score'] * self.weights['efficiency']
        )
        
        # 生成信号灯
        store_df['traffic_light'] = store_df['health_score'].apply(self.get_traffic_light_status)
        
        # 排序
        store_df = store_df.sort_values('health_score', ascending=False)
        
        return store_df
    
    def get_traffic_light_status(self, score: float) -> str:
        """
        根据评分获取信号灯状态
        
        Args:
            score: 健康度评分
            
        Returns:
            信号灯状态 ('🟢' / '🟡' / '🔴')
        """
        if score >= TRAFFIC_LIGHT_THRESHOLDS['green']:
            return '🟢'
        elif score >= TRAFFIC_LIGHT_THRESHOLDS['yellow']:
            return '🟡'
        else:
            return '🔴'
    
    def get_traffic_light_label(self, status: str) -> str:
        """
        获取信号灯标签
        
        Args:
            status: 信号灯状态
            
        Returns:
            标签文本
        """
        labels = {
            '🟢': '健康',
            '🟡': '需关注',
            '🔴': '高危'
        }
        return labels.get(status, '未知')
    
    def analyze_financial_health(self, df: pd.DataFrame,
                                  store_col: str = 'brand_store_name') -> Dict[str, Any]:
        """
        分析财务健康度
        
        检测：
        - 到手率是否低于行业基准
        - 实收增长是否源于单量增加还是客单价提升
        - 是否存在"增收不增利"
        
        Args:
            df: 数据
            store_col: 门店列名
            
        Returns:
            财务健康度分析结果
        """
        if df.empty:
            return {"error": "数据为空"}
        
        results = {}
        
        # 按门店聚合
        agg_df = df.groupby(store_col).agg({
            'actual_income': 'sum',
            'turnover': 'sum' if 'turnover' in df.columns else 'sum',
            'valid_orders': 'sum'
        }).reset_index() if 'actual_income' in df.columns else pd.DataFrame()
        
        if agg_df.empty:
            return {"error": "缺少财务数据"}
        
        for _, row in agg_df.iterrows():
            store = row[store_col]
            
            store_result = {
                'actual_income': float(row.get('actual_income', 0)),
                'valid_orders': int(row.get('valid_orders', 0)),
                'issues': [],
                'status': 'healthy'
            }
            
            # 计算到手率
            turnover = row.get('turnover', 0)
            actual_income = row.get('actual_income', 0)
            
            if turnover and turnover > 0:
                margin_rate = actual_income / turnover * 100
                store_result['margin_rate'] = round(margin_rate, 2)
                
                # 检查是否低于基准
                if margin_rate < INDUSTRY_BENCHMARKS['margin_rate']:
                    store_result['issues'].append({
                        'type': 'low_margin_rate',
                        'message': f"到手率 {margin_rate:.1f}% 低于行业基准 {INDUSTRY_BENCHMARKS['margin_rate']}%",
                        'severity': 'high' if margin_rate < 50 else 'medium'
                    })
                    store_result['status'] = 'warning'
            
            # 计算客单价
            if row.get('valid_orders', 0) > 0:
                avg_order_value = actual_income / row['valid_orders']
                store_result['avg_order_value'] = round(avg_order_value, 2)
            
            results[store] = store_result
        
        # 检测增收不增利（需要时间段对比）
        if 'date' in df.columns:
            revenue_profit_analysis = self._detect_revenue_profit_gap(df, store_col)
            for store, analysis in revenue_profit_analysis.items():
                if store in results:
                    results[store]['revenue_profit_gap'] = analysis
        
        return results
    
    def analyze_operational_compliance(self, df: pd.DataFrame,
                                        store_col: str = 'brand_store_name') -> Dict[str, Any]:
        """
        分析运营合规性
        
        检测：
        - 非异率/商责订单情况
        - 回复率合格情况
        - 出餐上报率
        
        Args:
            df: 数据
            store_col: 门店列名
            
        Returns:
            运营合规性分析结果
        """
        if df.empty:
            return {"error": "数据为空"}
        
        results = {}
        
        # 使用红线检测器
        redline_result = self.redline_detector.detect_all(df)
        
        # 按门店组织结果
        for store in df[store_col].unique():
            store_violations = redline_result['by_store'].get(store, [])
            
            # 筛选合规相关违规
            compliance_violations = [
                v for v in store_violations
                if v['type'] in ['merchant_responsibility', 'merchant_cancellation_rate',
                                 'reply_rate_5min', 'reply_rate_1min', 'meal_report_rate']
            ]
            
            # 计算合规评分
            compliance_score = 100
            for v in compliance_violations:
                if v['severity'] == 'high':
                    compliance_score -= 20
                elif v['severity'] == 'medium':
                    compliance_score -= 10
                else:
                    compliance_score -= 5
            
            compliance_score = max(0, compliance_score)
            
            results[store] = {
                'compliance_score': compliance_score,
                'status': 'compliant' if compliance_score >= 80 else ('warning' if compliance_score >= 60 else 'non_compliant'),
                'violations': compliance_violations,
                'violation_count': len(compliance_violations)
            }
        
        return results
    
    def analyze_reputation_quality(self, df: pd.DataFrame,
                                    store_col: str = 'brand_store_name') -> Dict[str, Any]:
        """
        分析口碑与质量
        
        检测：
        - 店铺评分
        - 商品满意度
        - 包装满意度
        - 食安/服务负反馈
        
        Args:
            df: 数据
            store_col: 门店列名
            
        Returns:
            口碑与质量分析结果
        """
        if df.empty:
            return {"error": "数据为空"}
        
        results = {}
        
        # 按门店聚合口碑指标
        agg_rules = {}
        if 'store_score' in df.columns:
            agg_rules['store_score'] = 'mean'
        if 'product_satisfaction' in df.columns:
            agg_rules['product_satisfaction'] = 'mean'
        if 'packaging_satisfaction' in df.columns:
            agg_rules['packaging_satisfaction'] = 'mean'
        if 'food_safety_negative_feedback_rate' in df.columns:
            agg_rules['food_safety_negative_feedback_rate'] = 'max'
        if 'service_negative_feedback_score' in df.columns:
            agg_rules['service_negative_feedback_score'] = 'mean'
        
        if agg_rules:
            agg_df = df.groupby(store_col).agg(agg_rules).reset_index()
        else:
            return {"error": "缺少口碑数据"}
        
        for _, row in agg_df.iterrows():
            store = row[store_col]
            
            store_result = {
                'metrics': {},
                'issues': [],
                'status': 'good'
            }
            
            # 店铺评分
            if 'store_score' in row and pd.notna(row['store_score']):
                score = row['store_score']
                store_result['metrics']['store_score'] = round(score, 2)
                
                if score < 4.0:
                    store_result['issues'].append({
                        'type': 'low_store_score',
                        'message': f"店铺评分 {score:.2f} 严重偏低",
                        'severity': 'high'
                    })
                    store_result['status'] = 'critical'
                elif score < 4.2:
                    store_result['issues'].append({
                        'type': 'low_store_score',
                        'message': f"店铺评分 {score:.2f} 偏低",
                        'severity': 'medium'
                    })
                    store_result['status'] = 'warning'
            
            # 商品满意度
            if 'product_satisfaction' in row and pd.notna(row['product_satisfaction']):
                satisfaction = row['product_satisfaction']
                store_result['metrics']['product_satisfaction'] = round(satisfaction, 1)
                
                if satisfaction < 80:
                    store_result['issues'].append({
                        'type': 'low_product_satisfaction',
                        'message': f"商品满意度 {satisfaction:.1f}% 偏低",
                        'severity': 'medium'
                    })
            
            # 包装满意度
            if 'packaging_satisfaction' in row and pd.notna(row['packaging_satisfaction']):
                satisfaction = row['packaging_satisfaction']
                store_result['metrics']['packaging_satisfaction'] = round(satisfaction, 1)
                
                if satisfaction < 80:
                    store_result['issues'].append({
                        'type': 'low_packaging_satisfaction',
                        'message': f"包装满意度 {satisfaction:.1f}% 偏低，可能存在撒漏问题",
                        'severity': 'medium'
                    })
            
            # 食安负反馈
            if 'food_safety_negative_feedback_rate' in row and pd.notna(row['food_safety_negative_feedback_rate']):
                rate = row['food_safety_negative_feedback_rate']
                if rate > 0:
                    store_result['metrics']['food_safety_issue'] = True
                    store_result['issues'].append({
                        'type': 'food_safety',
                        'message': f"存在食品安全负反馈",
                        'severity': 'high'
                    })
                    store_result['status'] = 'critical'
            
            results[store] = store_result
        
        return results
    
    def generate_store_health_report(self, df: pd.DataFrame,
                                      store_name: str) -> Dict[str, Any]:
        """
        生成单个门店的完整健康报告
        
        Args:
            df: 数据
            store_name: 门店名称
            
        Returns:
            完整健康报告
        """
        if df.empty:
            return {"error": "数据为空"}
        
        # 筛选门店数据
        store_df = df[df['brand_store_name'] == store_name]
        
        if store_df.empty:
            return {"error": f"未找到门店: {store_name}"}
        
        # 计算健康度评分
        health_df = self.calculate_health_score(store_df)
        
        if health_df.empty:
            return {"error": "计算健康度失败"}
        
        health_data = health_df.iloc[0].to_dict()
        
        # 财务健康度
        financial = self.analyze_financial_health(store_df)
        financial_data = financial.get(store_name, {})
        
        # 运营合规性
        compliance = self.analyze_operational_compliance(store_df)
        compliance_data = compliance.get(store_name, {})
        
        # 口碑质量
        reputation = self.analyze_reputation_quality(store_df)
        reputation_data = reputation.get(store_name, {})
        
        # 红线违规
        redlines = self.redline_detector.get_store_redlines(df, store_name)
        
        return {
            'success': True,
            'store_name': store_name,
            'health_score': round(health_data.get('health_score', 0), 2),
            'traffic_light': health_data.get('traffic_light', '🔴'),
            'traffic_light_label': self.get_traffic_light_label(health_data.get('traffic_light', '🔴')),
            'dimension_scores': {
                'revenue': round(health_data.get('revenue_score', 0), 2),
                'compliance': round(health_data.get('compliance_score', 0), 2),
                'reputation': round(health_data.get('reputation_score', 0), 2),
                'efficiency': round(health_data.get('efficiency_score', 0), 2)
            },
            'financial_health': financial_data,
            'operational_compliance': compliance_data,
            'reputation_quality': reputation_data,
            'redlines': redlines,
            'recommendations': self._generate_recommendations(health_data, redlines)
        }
    
    def generate_all_stores_report(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        生成所有门店的健康报告摘要
        
        Args:
            df: 数据
            
        Returns:
            所有门店健康报告摘要
        """
        if df.empty:
            return {"error": "数据为空"}
        
        # 计算所有门店健康度
        health_df = self.calculate_health_score(df)
        
        if health_df.empty:
            return {"error": "计算健康度失败"}
        
        # 统计信号灯分布
        traffic_light_dist = health_df['traffic_light'].value_counts().to_dict()
        
        # 高危门店列表
        high_risk = health_df[health_df['traffic_light'] == '🔴'][['brand_store_name', 'health_score']].to_dict('records')
        
        # 需关注门店列表
        warning = health_df[health_df['traffic_light'] == '🟡'][['brand_store_name', 'health_score']].to_dict('records')
        
        # 最佳门店
        best = health_df[health_df['traffic_light'] == '🟢'].head(5)[['brand_store_name', 'health_score']].to_dict('records')
        
        return {
            'success': True,
            'total_stores': len(health_df),
            'traffic_light_distribution': {
                'green': traffic_light_dist.get('🟢', 0),
                'yellow': traffic_light_dist.get('🟡', 0),
                'red': traffic_light_dist.get('🔴', 0)
            },
            'average_health_score': round(health_df['health_score'].mean(), 2),
            'high_risk_stores': high_risk,
            'warning_stores': warning,
            'best_stores': best,
            'store_ranking': health_df[['brand_store_name', 'health_score', 'traffic_light']].to_dict('records')
        }
    
    def _calculate_revenue_score(self, row: pd.Series) -> float:
        """计算营收健康度评分"""
        score = 100.0
        
        # 基于实收金额
        actual_income = row.get('actual_income', 0)
        if actual_income <= 0:
            return 0
        
        # 实收越高，基础分越高（封顶 100）
        if actual_income >= 100000:
            base_score = 100
        elif actual_income >= 50000:
            base_score = 80
        elif actual_income >= 20000:
            base_score = 60
        elif actual_income >= 10000:
            base_score = 40
        else:
            base_score = 20
        
        return min(100, base_score)
    
    def _calculate_compliance_score(self, row: pd.Series, df: pd.DataFrame, 
                                     store: str, store_col: str) -> float:
        """计算合规性评分"""
        score = 100.0
        
        # 商责扣分
        merchant_cancelled = row.get('merchant_cancelled_orders', 0)
        if merchant_cancelled > 0:
            score -= min(30, merchant_cancelled * 10)
        
        # 回复率扣分
        reply_rate = row.get('five_min_reply_rate', 100)
        if reply_rate < 100:
            if reply_rate < 80:
                score -= 20
            elif reply_rate < 90:
                score -= 10
            else:
                score -= 5
        
        return max(0, score)
    
    def _calculate_reputation_score(self, row: pd.Series) -> float:
        """计算口碑评分"""
        score = 100.0
        
        # 店铺评分
        store_score = row.get('store_score', None)
        if pd.notna(store_score):
            if store_score < 4.0:
                score -= 40
            elif store_score < 4.2:
                score -= 25
            elif store_score < 4.5:
                score -= 10
        
        # 商品满意度
        product_sat = row.get('product_satisfaction', None)
        if pd.notna(product_sat):
            if product_sat < 80:
                score -= 15
            elif product_sat < 90:
                score -= 5
        
        # 包装满意度
        packaging_sat = row.get('packaging_satisfaction', None)
        if pd.notna(packaging_sat):
            if packaging_sat < 80:
                score -= 10
            elif packaging_sat < 90:
                score -= 5
        
        return max(0, score)
    
    def _calculate_efficiency_score(self, row: pd.Series) -> float:
        """计算效率评分"""
        score = 100.0
        
        # 到手率
        margin_rate = row.get('net_margin_rate', None)
        if pd.notna(margin_rate):
            if margin_rate < 50:
                score -= 30
            elif margin_rate < 55:
                score -= 20
            elif margin_rate < 60:
                score -= 10
        
        # 转化率
        conversion_rate = row.get('order_conversion_rate', None)
        if pd.notna(conversion_rate):
            if conversion_rate < 10:
                score -= 20
            elif conversion_rate < 15:
                score -= 10
        
        return max(0, score)
    
    def _detect_revenue_profit_gap(self, df: pd.DataFrame,
                                    store_col: str) -> Dict[str, Dict]:
        """
        检测增收不增利
        
        比较时间前半段和后半段的营收和利润变化
        """
        results = {}
        
        if 'date' not in df.columns:
            return results
        
        df = df.copy()
        df['date'] = pd.to_datetime(df['date'])
        
        # 分割时间段
        mid_date = df['date'].min() + (df['date'].max() - df['date'].min()) / 2
        
        first_half = df[df['date'] <= mid_date]
        second_half = df[df['date'] > mid_date]
        
        for store in df[store_col].unique():
            first_store = first_half[first_half[store_col] == store]
            second_store = second_half[second_half[store_col] == store]
            
            if first_store.empty or second_store.empty:
                continue
            
            # 计算收入变化
            first_revenue = first_store['actual_income'].sum() if 'actual_income' in first_store.columns else 0
            second_revenue = second_store['actual_income'].sum() if 'actual_income' in second_store.columns else 0
            
            revenue_change = ((second_revenue - first_revenue) / first_revenue * 100) if first_revenue > 0 else 0
            
            # 计算利润变化（用到手率估算）
            if 'turnover' in df.columns and 'actual_income' in df.columns:
                first_turnover = first_store['turnover'].sum()
                second_turnover = second_store['turnover'].sum()
                
                first_margin = (first_revenue / first_turnover * 100) if first_turnover > 0 else 0
                second_margin = (second_revenue / second_turnover * 100) if second_turnover > 0 else 0
                
                margin_change = second_margin - first_margin
                
                # 增收不增利：收入增长但到手率下降
                if revenue_change > 0 and margin_change < -2:
                    results[store] = {
                        'status': 'revenue_up_profit_down',
                        'revenue_change': round(revenue_change, 2),
                        'margin_change': round(margin_change, 2),
                        'message': f"增收不增利：收入增长 {revenue_change:.1f}%，但到手率下降 {abs(margin_change):.1f}%"
                    }
                else:
                    results[store] = {
                        'status': 'healthy',
                        'revenue_change': round(revenue_change, 2),
                        'margin_change': round(margin_change, 2)
                    }
        
        return results
    
    def _generate_recommendations(self, health_data: Dict, 
                                   redlines: List[Dict]) -> List[Dict]:
        """生成改进建议"""
        recommendations = []
        
        # 基于红线违规
        for redline in redlines[:3]:  # 最多3条
            rec = {
                'priority': 'P0' if redline['severity'] == 'high' else ('P1' if redline['severity'] == 'medium' else 'P2'),
                'issue': redline['name'],
                'action': self._get_action_for_issue(redline['type']),
                'expected_result': self._get_expected_result(redline['type'])
            }
            recommendations.append(rec)
        
        # 基于评分维度
        if health_data.get('revenue_score', 100) < 60:
            recommendations.append({
                'priority': 'P1',
                'issue': '营收偏低',
                'action': '优化菜单结构，提升高毛利产品占比；增加推广投入',
                'expected_result': '营收提升 20%'
            })
        
        if health_data.get('compliance_score', 100) < 60:
            recommendations.append({
                'priority': 'P0',
                'issue': '合规性不足',
                'action': '加强员工培训，完善操作SOP；设置回复率监控提醒',
                'expected_result': '商责降为0，回复率100%'
            })
        
        if health_data.get('reputation_score', 100) < 60:
            recommendations.append({
                'priority': 'P1',
                'issue': '口碑待提升',
                'action': '分析差评内容，针对性改进；优化包装防止撒漏',
                'expected_result': '评分提升至4.5以上'
            })
        
        # 按优先级排序
        recommendations.sort(key=lambda x: x['priority'])
        
        return recommendations[:5]  # 最多5条
    
    def _get_action_for_issue(self, issue_type: str) -> str:
        """获取针对问题的行动建议"""
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


def analyze_store_health(df: pd.DataFrame, 
                         store_name: str = None,
                         **kwargs) -> Dict[str, Any]:
    """
    便捷函数：分析门店健康度
    
    Args:
        df: 数据
        store_name: 门店名称，如果为 None 则返回所有门店报告
        **kwargs: 其他参数
        
    Returns:
        健康度分析结果
    """
    analyzer = HealthAnalyzer()
    
    if store_name:
        return analyzer.generate_store_health_report(df, store_name)
    else:
        return analyzer.generate_all_stores_report(df)