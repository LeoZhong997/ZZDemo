# 简化的门店映射查看页面
# 直接从 daily_orders 表读取映射关系

import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from etl.config import get_connection_string

# 页面配置
st.set_page_config(
    page_title="门店映射",
    page_icon="🔗",
    layout="wide"
)

st.title("🔗 门店映射关系")
st.markdown("---")

# 创建数据库连接
@st.cache_resource
def get_engine():
    return create_engine(get_connection_string())

engine = get_engine()


# 加载门店映射关系
@st.cache_data(ttl=300)
def load_store_mappings(start_date, end_date):
    with engine.connect() as conn:
        query = text("""
            SELECT DISTINCT 
                platform,
                brand_store_name,
                platform_store_name,
                COUNT(*) as record_count,
                MIN(date) as first_date,
                MAX(date) as last_date
            FROM daily_orders 
            WHERE date BETWEEN :start_date AND :end_date
                AND platform_store_name IS NOT NULL
                AND brand_store_name IS NOT NULL
            GROUP BY platform, brand_store_name, platform_store_name
            ORDER BY platform, brand_store_name, platform_store_name
        """)
        result = conn.execute(query, {'start_date': start_date, 'end_date': end_date})
        return pd.DataFrame(result.fetchall(), columns=result.keys())


# 主界面
def main():
    # 侧边栏：日期范围选择
    with st.sidebar:
        st.header("📅 日期范围")
        
        # 默认日期范围
        default_start = pd.to_datetime('2026-01-05').date()
        default_end = pd.to_datetime('2026-01-11').date()
        
        start_date = st.date_input("开始日期", value=default_start)
        end_date = st.date_input("结束日期", value=default_end)
        
        if start_date > end_date:
            st.error("⚠️ 开始日期不能大于结束日期")
            st.stop()
    
    # 加载数据
    df_mappings = load_store_mappings(start_date, end_date)
    
    # 统计信息
    st.subheader("📊 映射关系统计")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("总映射数", len(df_mappings))
    with col2:
        brand_count = df_mappings['brand_store_name'].nunique()
        st.metric("品牌门店数", brand_count)
    with col3:
        platform_count = df_mappings['platform'].nunique()
        st.metric("平台数", platform_count)
    with col4:
        total_records = df_mappings['record_count'].sum()
        st.metric("总记录数", f"{total_records:,}")
    
    st.markdown("---")
    
    # 按平台分组显示映射关系
    st.subheader("🏪 各平台映射关系")
    
    platforms = sorted(df_mappings['platform'].unique())
    
    if platforms:
        tabs = st.tabs(platforms)
        
        for i, platform in enumerate(platforms):
            with tabs[i]:
                # 获取当前平台的数据
                df_platform = df_mappings[df_mappings['platform'] == platform].copy()
                
                # 按品牌门店分组
                df_grouped = df_platform.groupby('brand_store_name').agg({
                    'platform_store_name': list,
                    'record_count': list,
                    'first_date': 'min',
                    'last_date': 'max'
                }).reset_index()
                
                # 展开平台门店列表
                df_expanded = df_platform.groupby('brand_store_name').agg({
                    'platform_store_name': lambda x: ', '.join(sorted(set(x))),
                    'record_count': 'sum',
                    'first_date': 'min',
                    'last_date': 'max'
                }).reset_index()
                
                st.dataframe(
                    df_expanded,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "brand_store_name": "品牌门店名称",
                        "platform_store_name": "平台门店名称",
                        "record_count": "记录数",
                        "first_date": "首次出现",
                        "last_date": "最后出现"
                    }
                )
                
                # 显示详细映射表
                with st.expander(f"查看 {platform} 详细映射表"):
                    st.dataframe(
                        df_platform,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "brand_store_name": "品牌门店名称",
                            "platform_store_name": "平台门店名称",
                            "record_count": "记录数",
                            "first_date": "首次出现",
                            "last_date": "最后出现"
                        }
                    )
    
    # 导出功能
    st.markdown("---")
    st.subheader("💾 导出数据")
    
    col1, col2 = st.columns(2)
    with col1:
        # 导出所有映射关系
        csv_export = df_mappings.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 导出所有映射关系 (CSV)",
            data=csv_export,
            file_name=f"store_mappings_{start_date}_{end_date}.csv",
            mime="text/csv"
        )
    
    with col2:
        # 按平台分别导出
        if platforms:
            for platform in platforms:
                df_platform = df_mappings[df_mappings['platform'] == platform]
                csv_export = df_platform.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label=f"📥 导出 {platform} 映射 (CSV)",
                    data=csv_export,
                    file_name=f"store_mappings_{platform}_{start_date}_{end_date}.csv",
                    mime="text/csv"
                )
    
    # 使用说明
    st.markdown("---")
    st.info("""
    💡 **使用说明**：
    
    - 本页面直接从 daily_orders 表读取品牌门店名称与平台门店名称的映射关系
    - 可以通过调整日期范围来查看不同时间段的映射关系
    - 支持按平台分类查看和导出数据
    - 每个品牌门店可能对应多个平台门店名称
    
    📌 **注意事项**：
    - 映射关系来源于实际导入的数据
    - 如果映射关系有误，需要在源文件中修正后再重新导入
    - 同一品牌门店在不同平台可能有不同的门店名称
    """)


if __name__ == "__main__":
    main()