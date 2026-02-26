"""
时间序列分析器
提供日度聚合、趋势计算、周期性分析功能
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import logging

from ai.config import get_ai_config

logger = logging.getLogger(__name__)


class TimeSeriesAnalyzer:
    """
    时间序列分析器
    
    功能：
    - 日度聚合
    - 趋势计算
    - 周期性分析
    """
    
    def __init__(self):
        """初始化时间序列分析器"""
        self.config = get_ai_config('analysis', {})
    
    def _ensure_derived_metric(self, df: pd.DataFrame, metric: str) -> pd.DataFrame:
        """
        确保衍生指标存在，如果不存在则计算
        
        Args:
            df: 原始数据
            metric: 需要的指标名
            
        Returns:
            添加了衍生指标的数据
        """
        df = df.copy()
        
        # 到手率/利润率相关指标
        margin_metrics = ['net_margin_rate', 'margin_rate', 'profit_rate', 'real_net_margin_rate']
        
        if metric in margin_metrics:
            # 检查列是否已存在且有效数据不为空
            if metric in df.columns:
                valid_count = df[metric].notna().sum()
                if valid_count > 0:
                    return df  # 数据已存在且有效
            
            # 尝试从 actual_income 和 turnover (营业额) 计算
            if 'actual_income' in df.columns and 'turnover' in df.columns:
                df[metric] = df.apply(
                    lambda row: (row['actual_income'] / row['turnover'] * 100)
                    if pd.notna(row.get('turnover')) and row.get('turnover', 0) > 0 
                    else np.nan,
                    axis=1
                )
            # 备选：从 actual_income 和 platform_revenue 计算
            elif 'actual_income' in df.columns and 'platform_revenue' in df.columns:
                df[metric] = df.apply(
                    lambda row: (row['actual_income'] / row['platform_revenue'] * 100)
                    if pd.notna(row.get('platform_revenue')) and row.get('platform_revenue', 0) > 0 
                    else np.nan,
                    axis=1
                )
        
        return df
    
    def aggregate_daily(self, df: pd.DataFrame,
                        metric: str = 'actual_income',
                        date_col: str = 'date') -> pd.DataFrame:
        """
        按日聚合数据
        
        Args:
            df: 原始数据
            metric: 聚合指标
            date_col: 日期列名
            
        Returns:
            日度聚合数据
        """
        if df.empty:
            return pd.DataFrame()
        
        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col])
        
        # 确保衍生指标存在
        df = self._ensure_derived_metric(df, metric)
        
        # 根据指标类型选择聚合方式
        # 百分比类型和比率类型使用 mean，其他使用 sum
        mean_metrics = [
            'net_margin_rate', 'real_net_margin_rate',  # 到手率
            'merchant_cancellation_rate',  # 取消率
            'store_entry_rate', 'order_conversion_rate',  # 转化率
            'new_customer_entry_rate', 'new_customer_order_rate',
            'old_customer_entry_rate', 'old_customer_order_rate',
            'repurchase_rate',  # 复购率
            'store_score',  # 评分
            'avg_paid_price',  # 均价
        ]
        
        # 检查是否为百分比/比率类型指标
        is_rate_metric = any(rate_key in metric.lower() for rate_key in ['rate', 'score', 'avg'])
        if metric in mean_metrics or is_rate_metric:
            agg_func = 'mean'
        else:
            agg_func = 'sum'
        
        daily = df.groupby(date_col)[metric].agg(agg_func).reset_index()
        daily = daily.sort_values(date_col)
        
        # 处理 NaN 值
        daily = daily.dropna(subset=[metric])
        
        # 添加日期特征
        daily['day_of_week'] = daily[date_col].dt.dayofweek
        daily['day_name'] = daily[date_col].dt.day_name()
        daily['is_weekend'] = daily['day_of_week'].isin([5, 6])
        
        return daily
    
    def aggregate_weekly(self, df: pd.DataFrame,
                          metric: str = 'actual_income',
                          date_col: str = 'date') -> pd.DataFrame:
        """
        按周聚合数据
        
        Args:
            df: 原始数据
            metric: 聚合指标
            date_col: 日期列名
            
        Returns:
            周度聚合数据
        """
        if df.empty:
            return pd.DataFrame()
        
        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col])
        
        # 添加年-周标识
        df['year_week'] = df[date_col].dt.strftime('%Y-W%W')
        
        weekly = df.groupby('year_week')[metric].sum().reset_index()
        weekly = weekly.sort_values('year_week')
        
        return weekly
    
    def calculate_trend(self, daily_data: pd.DataFrame,
                        metric: str = 'actual_income',
                        date_col: str = 'date') -> Dict[str, Any]:
        """
        计算趋势
        
        Args:
            daily_data: 日度数据
            metric: 分析指标
            date_col: 日期列名
            
        Returns:
            {
                "direction": "上升/下降/平稳",
                "strength": 趋势强度 (0-1),
                "daily_change": 日均变化量,
                "slope": 斜率,
                "r_squared": R² 拟合度
            }
        """
        if daily_data.empty or metric not in daily_data.columns:
            return {"direction": "未知", "strength": 0}
        
        df = daily_data.copy()
        df = df.sort_values(date_col)
        
        # 准备数据
        x = np.arange(len(df))
        y = df[metric].values
        
        if len(x) < 2:
            return {"direction": "数据不足", "strength": 0}
        
        # 线性回归
        try:
            slope, intercept = np.polyfit(x, y, 1)
            
            # 计算 R²
            y_pred = slope * x + intercept
            ss_res = np.sum((y - y_pred) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
            
            # 日均变化
            daily_change = slope
            
            # 趋势强度（基于斜率相对于均值的比例）
            mean_value = np.mean(y)
            strength = min(1.0, abs(slope) / (mean_value + 1e-6) * 100) if mean_value > 0 else 0
            
            # 判断方向
            if slope > 0 and strength > 0.01:
                direction = "上升"
            elif slope < 0 and strength > 0.01:
                direction = "下降"
            else:
                direction = "平稳"
            
            return {
                "direction": direction,
                "strength": round(strength, 4),
                "daily_change": round(daily_change, 2),
                "slope": round(slope, 4),
                "r_squared": round(r_squared, 4),
                "trend_line": {
                    "start": round(intercept, 2),
                    "end": round(intercept + slope * len(x), 2)
                }
            }
            
        except Exception as e:
            logger.error(f"趋势计算失败: {e}")
            return {"direction": "计算失败", "strength": 0}
    
    def detect_seasonality(self, df: pd.DataFrame,
                           metric: str = 'actual_income',
                           date_col: str = 'date') -> Dict[str, Any]:
        """
        检测周期性（主要检测周模式）
        
        Args:
            df: 数据
            metric: 分析指标
            date_col: 日期列名
            
        Returns:
            {
                "has_weekly_pattern": bool,
                "peak_day": 高峰日,
                "low_day": 低谷日,
                "weekday_avg": 各日均值,
                "weekend_effect": 周末效应
            }
        """
        if df.empty or metric not in df.columns:
            return {"has_weekly_pattern": False}
        
        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col])
        df['day_of_week'] = df[date_col].dt.dayofweek
        
        # 按星期几聚合
        weekday_stats = df.groupby('day_of_week')[metric].agg(['mean', 'std', 'count']).reset_index()
        
        if len(weekday_stats) < 7:
            return {"has_weekly_pattern": False, "message": "数据不完整，无法分析周期性"}
        
        # 星期名称映射
        day_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
        weekday_stats['day_name'] = weekday_stats['day_of_week'].apply(lambda x: day_names[x])
        
        # 找出高峰和低谷
        peak_idx = weekday_stats['mean'].idxmax()
        low_idx = weekday_stats['mean'].idxmin()
        
        peak_day = day_names[int(weekday_stats.loc[peak_idx, 'day_of_week'])]
        low_day = day_names[int(weekday_stats.loc[low_idx, 'day_of_week'])]
        
        # 计算周期性强度（最高/最低的比值）
        peak_value = weekday_stats.loc[peak_idx, 'mean']
        low_value = weekday_stats.loc[low_idx, 'mean']
        
        if low_value > 0:
            pattern_strength = peak_value / low_value
        else:
            pattern_strength = 1.0
        
        # 判断是否有明显的周模式
        has_pattern = pattern_strength > 1.2  # 高峰比低谷高20%以上
        
        # 周末效应
        weekday_avg = weekday_stats[weekday_stats['day_of_week'] < 5]['mean'].mean()
        weekend_avg = weekday_stats[weekday_stats['day_of_week'] >= 5]['mean'].mean()
        
        if weekday_avg > 0:
            weekend_effect = ((weekend_avg - weekday_avg) / weekday_avg) * 100
        else:
            weekend_effect = 0
        
        weekday_avgs = {}
        for _, row in weekday_stats.iterrows():
            weekday_avgs[day_names[int(row['day_of_week'])]] = round(row['mean'], 2)
        
        return {
            "has_weekly_pattern": has_pattern,
            "pattern_strength": round(pattern_strength, 2),
            "peak_day": peak_day,
            "peak_value": round(peak_value, 2),
            "low_day": low_day,
            "low_value": round(low_value, 2),
            "weekday_avg": weekday_avgs,
            "weekend_effect": round(weekend_effect, 2),
            "weekend_effect_label": "周末高于工作日" if weekend_effect > 5 else (
                "周末低于工作日" if weekend_effect < -5 else "周末与工作日持平"
            )
        }
    
    def calculate_moving_average(self, df: pd.DataFrame,
                                  metric: str = 'actual_income',
                                  date_col: str = 'date',
                                  windows: List[int] = [7, 14, 30]) -> pd.DataFrame:
        """
        计算移动平均
        
        Args:
            df: 数据
            metric: 指标
            date_col: 日期列名
            windows: 窗口大小列表
            
        Returns:
            添加了移动平均列的数据
        """
        if df.empty:
            return pd.DataFrame()
        
        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col])
        df = df.sort_values(date_col)
        
        # 先按日期聚合
        daily = df.groupby(date_col)[metric].sum().reset_index()
        
        for window in windows:
            if len(daily) >= window:
                daily[f'ma_{window}'] = daily[metric].rolling(window=window, min_periods=1).mean()
        
        return daily
    
    def calculate_volatility(self, df: pd.DataFrame,
                             metric: str = 'actual_income',
                             date_col: str = 'date',
                             window: int = 7) -> Dict[str, Any]:
        """
        计算波动性
        
        Args:
            df: 数据
            metric: 指标
            date_col: 日期列名
            window: 滚动窗口
            
        Returns:
            波动性指标
        """
        if df.empty:
            return {"volatility": 0}
        
        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col])
        
        # 按日期聚合
        daily = df.groupby(date_col)[metric].sum().reset_index()
        daily = daily.sort_values(date_col)
        
        if len(daily) < window:
            return {"volatility": 0, "message": "数据不足"}
        
        # 计算滚动标准差和变异系数
        daily['rolling_std'] = daily[metric].rolling(window=window).std()
        daily['rolling_mean'] = daily[metric].rolling(window=window).mean()
        daily['cv'] = daily['rolling_std'] / daily['rolling_mean'] * 100  # 变异系数
        
        # 整体波动性
        overall_cv = daily['cv'].dropna().mean() if not daily['cv'].dropna().empty else 0
        
        # 波动等级
        if overall_cv < 10:
            level = "低波动"
        elif overall_cv < 20:
            level = "中等波动"
        elif overall_cv < 30:
            level = "较高波动"
        else:
            level = "高波动"
        
        return {
            "volatility": round(overall_cv, 2),
            "level": level,
            "max_cv": round(daily['cv'].max(), 2) if not daily['cv'].empty else 0,
            "min_cv": round(daily['cv'].min(), 2) if not daily['cv'].empty else 0
        }
    
    def analyze_growth_periods(self, df: pd.DataFrame,
                                metric: str = 'actual_income',
                                date_col: str = 'date') -> Dict[str, Any]:
        """
        分析增长期和衰退期
        
        Args:
            df: 数据
            metric: 指标
            date_col: 日期列名
            
        Returns:
            增长期分析结果
        """
        if df.empty:
            return {}
        
        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col])
        
        # 按日期聚合
        daily = df.groupby(date_col)[metric].sum().reset_index()
        daily = daily.sort_values(date_col)
        
        if len(daily) < 3:
            return {"message": "数据不足"}
        
        # 计算日变化
        daily['change'] = daily[metric].diff()
        daily['is_growth'] = daily['change'] > 0
        
        # 统计增长和下降天数
        growth_days = daily['is_growth'].sum()
        decline_days = len(daily) - growth_days - 1  # 减去第一天（无变化）
        
        # 最长连续增长/下降
        max_growth_streak = 0
        max_decline_streak = 0
        current_streak = 0
        current_type = None
        
        for is_growth in daily['is_growth'].dropna():
            if current_type is None:
                current_type = is_growth
                current_streak = 1
            elif is_growth == current_type:
                current_streak += 1
            else:
                if current_type:
                    max_growth_streak = max(max_growth_streak, current_streak)
                else:
                    max_decline_streak = max(max_decline_streak, current_streak)
                current_type = is_growth
                current_streak = 1
        
        # 更新最后的streak
        if current_type:
            max_growth_streak = max(max_growth_streak, current_streak)
        else:
            max_decline_streak = max(max_decline_streak, current_streak)
        
        # 增长率
        total_days = len(daily) - 1
        growth_rate = growth_days / total_days * 100 if total_days > 0 else 0
        
        return {
            "total_days": total_days,
            "growth_days": int(growth_days),
            "decline_days": int(decline_days),
            "growth_rate": round(growth_rate, 2),
            "max_growth_streak": max_growth_streak,
            "max_decline_streak": max_decline_streak,
            "overall_trend": "增长" if growth_rate > 55 else ("下降" if growth_rate < 45 else "平稳")
        }
    
    def forecast_simple(self, df: pd.DataFrame,
                         metric: str = 'actual_income',
                         date_col: str = 'date',
                         days: int = 7) -> Dict[str, Any]:
        """
        简单预测（基于趋势的线性外推）
        
        Args:
            df: 数据
            metric: 指标
            date_col: 日期列名
            days: 预测天数
            
        Returns:
            预测结果
        """
        if df.empty:
            return {"error": "数据为空"}
        
        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col])
        
        # 按日期聚合
        daily = df.groupby(date_col)[metric].sum().reset_index()
        daily = daily.sort_values(date_col)
        
        if len(daily) < 3:
            return {"error": "数据点不足"}
        
        # 计算趋势
        trend = self.calculate_trend(daily, metric, date_col)
        
        # 生成预测日期
        last_date = daily[date_col].max()
        future_dates = [last_date + timedelta(days=i+1) for i in range(days)]
        
        # 基于趋势预测
        last_value = daily[metric].iloc[-1]
        slope = trend.get('slope', 0)
        
        predictions = []
        for i, date in enumerate(future_dates):
            pred_value = last_value + slope * (i + 1)
            # 确保预测值不为负
            pred_value = max(0, pred_value)
            
            predictions.append({
                "date": str(date.date()),
                "day_name": date.strftime('%A'),
                "predicted_value": round(pred_value, 2)
            })
        
        # 计算预测区间（基于历史波动）
        std = daily[metric].std()
        
        return {
            "method": "linear_trend",
            "trend": trend,
            "predictions": predictions,
            "total_predicted": round(sum(p['predicted_value'] for p in predictions), 2),
            "confidence_interval": {
                "lower": round(std * 0.5, 2),
                "upper": round(std * 1.5, 2)
            },
            "disclaimer": "此为简单线性预测，仅供参考"
        }
    
    def get_time_series_summary(self, df: pd.DataFrame,
                                 metric: str = 'actual_income',
                                 date_col: str = 'date') -> Dict[str, Any]:
        """
        获取时间序列综合分析摘要
        
        Args:
            df: 数据
            metric: 指标
            date_col: 日期列名
            
        Returns:
            综合分析摘要
        """
        if df.empty:
            return {"error": "数据为空"}
        
        # 聚合日度数据
        daily = self.aggregate_daily(df, metric, date_col)
        
        # 趋势分析
        trend = self.calculate_trend(daily, metric, date_col)
        
        # 周期性分析
        seasonality = self.detect_seasonality(df, metric, date_col)
        
        # 波动性分析
        volatility = self.calculate_volatility(df, metric, date_col)
        
        # 增长期分析
        growth_periods = self.analyze_growth_periods(df, metric, date_col)
        
        return {
            "date_range": {
                "start": str(daily[date_col].min().date()),
                "end": str(daily[date_col].max().date()),
                "days": len(daily)
            },
            "summary_stats": {
                "total": float(daily[metric].sum()),
                "mean": float(daily[metric].mean()),
                "max": float(daily[metric].max()),
                "min": float(daily[metric].min())
            },
            "trend": trend,
            "seasonality": seasonality,
            "volatility": volatility,
            "growth_periods": growth_periods
        }


def analyze_time_series(df: pd.DataFrame,
                         metric: str = 'actual_income',
                         analysis_type: str = 'summary',
                         **kwargs) -> Any:
    """
    便捷函数：时间序列分析
    
    Args:
        df: 数据
        metric: 指标
        analysis_type: 分析类型 (trend/seasonality/volatility/forecast/summary)
        **kwargs: 其他参数
        
    Returns:
        分析结果
    """
    analyzer = TimeSeriesAnalyzer()
    
    if analysis_type == 'trend':
        daily = analyzer.aggregate_daily(df, metric)
        return analyzer.calculate_trend(daily, metric)
    elif analysis_type == 'seasonality':
        return analyzer.detect_seasonality(df, metric)
    elif analysis_type == 'volatility':
        return analyzer.calculate_volatility(df, metric)
    elif analysis_type == 'forecast':
        days = kwargs.get('days', 7)
        return analyzer.forecast_simple(df, metric, days=days)
    elif analysis_type == 'summary':
        return analyzer.get_time_series_summary(df, metric)
    else:
        raise ValueError(f"不支持的分析类型: {analysis_type}")