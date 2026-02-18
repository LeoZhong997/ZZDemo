# 门店管理界面
# 用于管理品牌门店信息

import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from etl.config import get_connection_string

# 页面配置
st.set_page_config(
    page_title="门店管理",
    page_icon="🏪",
    layout="wide"
)

st.title("🏪 门店管理系统")
st.markdown("---")

# 创建数据库连接
@st.cache_resource
def get_engine():
    return create_engine(get_connection_string())

engine = get_engine()


# 加载品牌门店数据
@st.cache_data(ttl=300)
def load_brand_stores():
    with engine.connect() as conn:
        query = text("""
            SELECT 
                id,
                brand_store_name,
                store_address,
                store_type,
                open_date,
                contact_phone,
                contact_person,
                status,
                created_time,
                updated_time
            FROM brand_stores
            ORDER BY status, brand_store_name
        """)
        result = conn.execute(query)
        return pd.DataFrame(result.fetchall(), columns=result.keys())


# 添加品牌门店
def add_brand_store(name, address, store_type, open_date, phone, person, status):
    try:
        with engine.connect() as conn:
            query = text("""
                INSERT INTO brand_stores 
                (brand_store_name, store_address, store_type, open_date, contact_phone, contact_person, status)
                VALUES (:name, :address, :type, :date, :phone, :person, :status)
            """)
            conn.execute(query, {
                'name': name,
                'address': address,
                'type': store_type,
                'date': open_date,
                'phone': phone,
                'person': person,
                'status': status
            })
            conn.commit()
        return True, "✅ 门店添加成功"
    except Exception as e:
        return False, f"❌ 添加失败: {str(e)}"


# 更新品牌门店
def update_brand_store(store_id, name, address, store_type, open_date, phone, person, status):
    try:
        with engine.connect() as conn:
            query = text("""
                UPDATE brand_stores
                SET brand_store_name = :name,
                    store_address = :address,
                    store_type = :type,
                    open_date = :date,
                    contact_phone = :phone,
                    contact_person = :person,
                    status = :status
                WHERE id = :id
            """)
            conn.execute(query, {
                'name': name,
                'address': address,
                'type': store_type,
                'date': open_date,
                'phone': phone,
                'person': person,
                'status': status,
                'id': store_id
            })
            conn.commit()
        return True, "✅ 门店更新成功"
    except Exception as e:
        return False, f"❌ 更新失败: {str(e)}"


# 删除品牌门店
def delete_brand_store(store_id):
    try:
        with engine.connect() as conn:
            query = text("DELETE FROM brand_stores WHERE id = :id")
            conn.execute(query, {'id': store_id})
            conn.commit()
        return True, "✅ 门店删除成功"
    except Exception as e:
        return False, f"❌ 删除失败: {str(e)}"


# 主界面
def main():
    # 侧边栏：操作选择
    with st.sidebar:
        st.header("📋 操作菜单")
        operation = st.radio(
            "选择操作",
            ["📊 查看门店列表", "➕ 添加新门店", "✏️ 编辑门店", "🗑️ 删除门店"]
        )
    
    # 加载数据
    df_stores = load_brand_stores()
    
    # 操作1：查看门店列表
    if operation == "📊 查看门店列表":
        st.subheader("📊 门店列表")
        
        # 筛选选项
        col1, col2 = st.columns(2)
        with col1:
            status_filter = st.selectbox("门店状态", ["全部", "营业中", "关闭", "筹备中"])
        with col2:
            store_type_filter = st.selectbox("门店类型", ["全部"] + list(df_stores['store_type'].dropna().unique()))
        
        # 应用筛选
        df_filtered = df_stores.copy()
        if status_filter != "全部":
            df_filtered = df_filtered[df_filtered['status'] == status_filter]
        if store_type_filter != "全部":
            df_filtered = df_filtered[df_filtered['store_type'] == store_type_filter]
        
        # 显示数据
        st.dataframe(
            df_filtered,
            use_container_width=True,
            hide_index=True,
            column_config={
                "id": "ID",
                "brand_store_name": "门店名称",
                "store_address": "门店地址",
                "store_type": "门店类型",
                "open_date": "开店时间",
                "contact_phone": "联系电话",
                "contact_person": "联系人",
                "status": "状态",
                "created_time": "创建时间",
                "updated_time": "更新时间"
            }
        )
        
        # 统计信息
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("总门店数", len(df_stores))
        with col2:
            st.metric("营业中", len(df_stores[df_stores['status'] == '营业中']))
        with col3:
            st.metric("直营店", len(df_stores[df_stores['store_type'] == '直营店']))
        with col4:
            st.metric("加盟店", len(df_stores[df_stores['store_type'] == '加盟店']))
    
    # 操作2：添加新门店
    elif operation == "➕ 添加新门店":
        st.subheader("➕ 添加新门店")
        
        with st.form("add_store_form"):
            name = st.text_input("门店名称 *", max_chars=100)
            address = st.text_input("门店地址", max_chars=200)
            store_type = st.selectbox("门店类型", ["直营店", "加盟店", "其他"])
            open_date = st.date_input("开店时间")
            phone = st.text_input("联系电话", max_chars=20)
            person = st.text_input("联系人", max_chars=50)
            status = st.selectbox("状态", ["营业中", "关闭", "筹备中"])
            
            submitted = st.form_submit_button("添加门店")
            
            if submitted:
                if not name:
                    st.error("❌ 门店名称不能为空")
                else:
                    success, message = add_brand_store(name, address, store_type, open_date, phone, person, status)
                    if success:
                        st.success(message)
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(message)
    
    # 操作3：编辑门店
    elif operation == "✏️ 编辑门店":
        st.subheader("✏️ 编辑门店")
        
        # 选择要编辑的门店
        store_to_edit = st.selectbox(
            "选择要编辑的门店",
            options=df_stores['id'].tolist(),
            format_func=lambda x: f"{df_stores[df_stores['id'] == x]['brand_store_name'].values[0]} (ID: {x})"
        )
        
        if store_to_edit:
            # 获取门店信息
            store_info = df_stores[df_stores['id'] == store_to_edit].iloc[0]
            
            with st.form("edit_store_form"):
                name = st.text_input("门店名称 *", value=store_info['brand_store_name'], max_chars=100)
                address = st.text_input("门店地址", value=store_info['store_address'], max_chars=200)
                store_type = st.selectbox("门店类型", ["直营店", "加盟店", "其他"], 
                                       index=["直营店", "加盟店", "其他"].index(store_info['store_type']) if store_info['store_type'] in ["直营店", "加盟店", "其他"] else 0)
                open_date = st.date_input("开店时间", value=store_info['open_date'] if store_info['open_date'] else None)
                phone = st.text_input("联系电话", value=store_info['contact_phone'], max_chars=20)
                person = st.text_input("联系人", value=store_info['contact_person'], max_chars=50)
                status = st.selectbox("状态", ["营业中", "关闭", "筹备中"],
                                    index=["营业中", "关闭", "筹备中"].index(store_info['status']))
                
                submitted = st.form_submit_button("更新门店")
                
                if submitted:
                    if not name:
                        st.error("❌ 门店名称不能为空")
                    else:
                        success, message = update_brand_store(store_to_edit, name, address, store_type, open_date, phone, person, status)
                        if success:
                            st.success(message)
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error(message)
    
    # 操作4：删除门店
    elif operation == "🗑️ 删除门店":
        st.subheader("🗑️ 删除门店")
        
        st.warning("⚠️ 删除门店会同时删除该门店的所有映射关系，请谨慎操作！")
        
        # 选择要删除的门店
        store_to_delete = st.selectbox(
            "选择要删除的门店",
            options=df_stores['id'].tolist(),
            format_func=lambda x: f"{df_stores[df_stores['id'] == x]['brand_store_name'].values[0]} (ID: {x})"
        )
        
        if store_to_delete:
            store_info = df_stores[df_stores['id'] == store_to_delete].iloc[0]
            
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"门店名称: {store_info['brand_store_name']}")
                st.info(f"门店地址: {store_info['store_address']}")
            with col2:
                st.info(f"门店类型: {store_info['store_type']}")
                st.info(f"状态: {store_info['status']}")
            
            # 确认删除
            confirm = st.checkbox("我确认要删除此门店及其所有映射关系")
            
            if confirm:
                if st.button("确认删除", type="primary"):
                    success, message = delete_brand_store(store_to_delete)
                    if success:
                        st.success(message)
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(message)


if __name__ == "__main__":
    main()