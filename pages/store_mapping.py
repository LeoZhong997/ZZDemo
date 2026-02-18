# 门店映射管理界面
# 用于管理平台门店名称到品牌门店名称的映射关系

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

st.title("🔗 门店映射管理")
st.markdown("---")

# 创建数据库连接
@st.cache_resource
def get_engine():
    return create_engine(get_connection_string())

engine = get_engine()


# 加载品牌门店列表
@st.cache_data(ttl=300)
def load_brand_stores():
    with engine.connect() as conn:
        query = text("""
            SELECT id, brand_store_name, status
            FROM brand_stores
            ORDER BY brand_store_name
        """)
        result = conn.execute(query)
        return pd.DataFrame(result.fetchall(), columns=result.keys())


# 加载门店映射数据
@st.cache_data(ttl=300)
def load_store_mappings():
    with engine.connect() as conn:
        query = text("""
            SELECT 
                sm.id,
                sm.brand_store_id,
                bs.brand_store_name,
                sm.platform,
                sm.platform_store_name,
                sm.platform_store_id,
                sm.city,
                sm.is_active,
                sm.created_time,
                sm.updated_time
            FROM store_mapping sm
            INNER JOIN brand_stores bs ON sm.brand_store_id = bs.id
            ORDER BY sm.platform, bs.brand_store_name
        """)
        result = conn.execute(query)
        return pd.DataFrame(result.fetchall(), columns=result.keys())


# 添加门店映射
def add_store_mapping(brand_store_id, platform, platform_store_name, platform_store_id, city, is_active):
    try:
        with engine.connect() as conn:
            query = text("""
                INSERT INTO store_mapping 
                (brand_store_id, platform, platform_store_name, platform_store_id, city, is_active)
                VALUES (:brand_store_id, :platform, :platform_store_name, :platform_store_id, :city, :is_active)
            """)
            conn.execute(query, {
                'brand_store_id': brand_store_id,
                'platform': platform,
                'platform_store_name': platform_store_name,
                'platform_store_id': platform_store_id,
                'city': city,
                'is_active': 1 if is_active else 0
            })
            conn.commit()
        return True, "✅ 映射添加成功"
    except Exception as e:
        if "Duplicate entry" in str(e):
            return False, "❌ 该平台门店名称已存在映射"
        return False, f"❌ 添加失败: {str(e)}"


# 更新门店映射
def update_store_mapping(mapping_id, brand_store_id, platform, platform_store_name, platform_store_id, city, is_active):
    try:
        with engine.connect() as conn:
            query = text("""
                UPDATE store_mapping
                SET brand_store_id = :brand_store_id,
                    platform = :platform,
                    platform_store_name = :platform_store_name,
                    platform_store_id = :platform_store_id,
                    city = :city,
                    is_active = :is_active
                WHERE id = :id
            """)
            conn.execute(query, {
                'brand_store_id': brand_store_id,
                'platform': platform,
                'platform_store_name': platform_store_name,
                'platform_store_id': platform_store_id,
                'city': city,
                'is_active': 1 if is_active else 0,
                'id': mapping_id
            })
            conn.commit()
        return True, "✅ 映射更新成功"
    except Exception as e:
        return False, f"❌ 更新失败: {str(e)}"


# 删除门店映射
def delete_store_mapping(mapping_id):
    try:
        with engine.connect() as conn:
            query = text("DELETE FROM store_mapping WHERE id = :id")
            conn.execute(query, {'id': mapping_id})
            conn.commit()
        return True, "✅ 映射删除成功"
    except Exception as e:
        return False, f"❌ 删除失败: {str(e)}"


# 批量添加映射
def batch_add_mappings(df_mappings):
    """批量添加门店映射"""
    success_count = 0
    error_count = 0
    errors = []
    
    for idx, row in df_mappings.iterrows():
        try:
            # 查找品牌门店ID
            brand_store_name = row['品牌门店名称']
            with engine.connect() as conn:
                query = text("SELECT id FROM brand_stores WHERE brand_store_name = :name")
                result = conn.execute(query, {'name': brand_store_name})
                brand_row = result.fetchone()
                
                if brand_row:
                    brand_store_id = brand_row[0]
                else:
                    error_count += 1
                    errors.append(f"第{idx+2}行: 品牌门店 '{brand_store_name}' 不存在")
                    continue
                
            # 添加映射
            success, message = add_store_mapping(
                brand_store_id=brand_store_id,
                platform=row['平台'],
                platform_store_name=row['平台门店名称'],
                platform_store_id=row.get('平台门店ID', ''),
                city=row.get('城市', ''),
                is_active=True
            )
            
            if success:
                success_count += 1
            else:
                error_count += 1
                errors.append(f"第{idx+2}行: {message}")
                
        except Exception as e:
            error_count += 1
            errors.append(f"第{idx+2}行: {str(e)}")
    
    return success_count, error_count, errors


# 主界面
def main():
    # 侧边栏：操作选择
    with st.sidebar:
        st.header("📋 操作菜单")
        operation = st.radio(
            "选择操作",
            ["📊 查看映射列表", "➕ 添加映射", "📥 批量导入", "✏️ 编辑映射", "🗑️ 删除映射"]
        )
    
    # 加载数据
    df_brand_stores = load_brand_stores()
    df_mappings = load_store_mappings()
    
    # 操作1：查看映射列表
    if operation == "📊 查看映射列表":
        st.subheader("📊 门店映射列表")
        
        # 筛选选项
        col1, col2, col3 = st.columns(3)
        with col1:
            platform_filter = st.selectbox("平台", ["全部", "美团", "饿了么", "京东"])
        with col2:
            status_filter = st.selectbox("状态", ["全部", "启用", "禁用"])
        with col3:
            search = st.text_input("搜索门店名称")
        
        # 应用筛选
        df_filtered = df_mappings.copy()
        if platform_filter != "全部":
            df_filtered = df_filtered[df_filtered['platform'] == platform_filter]
        if status_filter != "全部":
            is_active_val = 1 if status_filter == "启用" else 0
            df_filtered = df_filtered[df_filtered['is_active'] == is_active_val]
        if search:
            df_filtered = df_filtered[
                df_filtered['brand_store_name'].str.contains(search, case=False, na=False) |
                df_filtered['platform_store_name'].str.contains(search, case=False, na=False)
            ]
        
        # 显示数据
        st.dataframe(
            df_filtered[[
                'id', 'brand_store_name', 'platform', 'platform_store_name',
                'platform_store_id', 'city', 'is_active', 'created_time'
            ]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "id": "ID",
                "brand_store_name": "品牌门店名称",
                "platform": "平台",
                "platform_store_name": "平台门店名称",
                "platform_store_id": "平台门店ID",
                "city": "城市",
                "is_active": st.column_config.CheckboxColumn("启用", help="是否启用此映射"),
                "created_time": "创建时间"
            }
        )
        
        # 统计信息
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("总映射数", len(df_mappings))
        with col2:
            st.metric("启用中", len(df_mappings[df_mappings['is_active'] == 1]))
        with col3:
            st.metric("美团", len(df_mappings[df_mappings['platform'] == '美团']))
    
    # 操作2：添加映射
    elif operation == "➕ 添加映射":
        st.subheader("➕ 添加门店映射")
        
        with st.form("add_mapping_form"):
            # 选择品牌门店
            brand_options = df_brand_stores[df_brand_stores['status'] == '营业中']['brand_store_name'].tolist()
            selected_brand = st.selectbox("品牌门店名称 *", brand_options)
            
            # 获取品牌门店ID
            brand_store_id = df_brand_stores[df_brand_stores['brand_store_name'] == selected_brand]['id'].values[0] if selected_brand else None
            
            platform = st.selectbox("平台 *", ["美团", "饿了么", "京东"])
            platform_store_name = st.text_input("平台门店名称 *", max_chars=100)
            platform_store_id = st.text_input("平台门店ID（如京东的门店id）", max_chars=50)
            city = st.text_input("门店所在城市", max_chars=100)
            is_active = st.checkbox("启用", value=True)
            
            submitted = st.form_submit_button("添加映射")
            
            if submitted:
                if not selected_brand or not platform or not platform_store_name:
                    st.error("❌ 请填写所有必填字段")
                else:
                    success, message = add_store_mapping(
                        brand_store_id, platform, platform_store_name,
                        platform_store_id, city, is_active
                    )
                    if success:
                        st.success(message)
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(message)
    
    # 操作3：批量导入
    elif operation == "📥 批量导入":
        st.subheader("📥 批量导入门店映射")
        
        st.markdown("""
        ### 📋 导入格式说明
        请上传Excel文件，包含以下列（表头）：
        - **品牌门店名称** (必填)
        - **平台** (必填，填：美团/饿了么/京东)
        - **平台门店名称** (必填)
        - **平台门店ID** (可选，如京东的门店id)
        - **城市** (可选)
        """)
        
        # 文件上传
        uploaded_file = st.file_uploader("上传Excel文件", type=['xlsx', 'xls'])
        
        if uploaded_file:
            try:
                df_import = pd.read_excel(uploaded_file)
                
                # 验证列名
                required_columns = ['品牌门店名称', '平台', '平台门店名称']
                missing_columns = [col for col in required_columns if col not in df_import.columns]
                
                if missing_columns:
                    st.error(f"❌ 缺少必填列: {', '.join(missing_columns)}")
                else:
                    # 显示预览
                    st.write("📊 数据预览:")
                    st.dataframe(df_import.head(10))
                    
                    # 确认导入
                    if st.button("开始导入", type="primary"):
                        success_count, error_count, errors = batch_add_mappings(df_import)
                        
                        st.success(f"✅ 导入完成！")
                        st.info(f"成功: {success_count} 条 | 失败: {error_count} 条")
                        
                        if errors:
                            with st.expander("查看错误详情"):
                                for error in errors[:20]:  # 只显示前20条错误
                                    st.error(error)
                                if len(errors) > 20:
                                    st.warning(f"... 还有 {len(errors) - 20} 条错误")
                        
                        if success_count > 0:
                            st.cache_data.clear()
                            if st.button("刷新数据"):
                                st.rerun()
            
            except Exception as e:
                st.error(f"❌ 读取文件失败: {str(e)}")
    
    # 操作4：编辑映射
    elif operation == "✏️ 编辑映射":
        st.subheader("✏️ 编辑门店映射")
        
        # 选择要编辑的映射
        mapping_to_edit = st.selectbox(
            "选择要编辑的映射",
            options=df_mappings['id'].tolist(),
            format_func=lambda x: f"{df_mappings[df_mappings['id'] == x]['brand_store_name'].values[0]} - {df_mappings[df_mappings['id'] == x]['platform'].values[0]} ({df_mappings[df_mappings['id'] == x]['platform_store_name'].values[0]}) [ID: {x}]"
        )
        
        if mapping_to_edit:
            # 获取映射信息
            mapping_info = df_mappings[df_mappings['id'] == mapping_to_edit].iloc[0]
            
            with st.form("edit_mapping_form"):
                # 选择品牌门店
                brand_options = df_brand_stores['brand_store_name'].tolist()
                selected_brand = st.selectbox(
                    "品牌门店名称 *",
                    brand_options,
                    index=brand_options.index(mapping_info['brand_store_name']) if mapping_info['brand_store_name'] in brand_options else 0
                )
                brand_store_id = df_brand_stores[df_brand_stores['brand_store_name'] == selected_brand]['id'].values[0]
                
                platform = st.selectbox("平台 *", ["美团", "饿了么", "京东"],
                                     index=["美团", "饿了么", "京东"].index(mapping_info['platform']))
                platform_store_name = st.text_input("平台门店名称 *", value=mapping_info['platform_store_name'], max_chars=100)
                platform_store_id = st.text_input("平台门店ID", value=mapping_info['platform_store_id'], max_chars=50)
                city = st.text_input("城市", value=mapping_info['city'], max_chars=100)
                is_active = st.checkbox("启用", value=bool(mapping_info['is_active']))
                
                submitted = st.form_submit_button("更新映射")
                
                if submitted:
                    if not selected_brand or not platform or not platform_store_name:
                        st.error("❌ 请填写所有必填字段")
                    else:
                        success, message = update_store_mapping(
                            mapping_to_edit, brand_store_id, platform, platform_store_name,
                            platform_store_id, city, is_active
                        )
                        if success:
                            st.success(message)
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error(message)
    
    # 操作5：删除映射
    elif operation == "🗑️ 删除映射":
        st.subheader("🗑️ 删除门店映射")
        
        st.warning("⚠️ 删除映射后，该平台门店名称将无法导入数据，请谨慎操作！")
        
        # 选择要删除的映射
        mapping_to_delete = st.selectbox(
            "选择要删除的映射",
            options=df_mappings['id'].tolist(),
            format_func=lambda x: f"{df_mappings[df_mappings['id'] == x]['brand_store_name'].values[0]} - {df_mappings[df_mappings['id'] == x]['platform'].values[0]} ({df_mappings[df_mappings['id'] == x]['platform_store_name'].values[0]}) [ID: {x}]"
        )
        
        if mapping_to_delete:
            mapping_info = df_mappings[df_mappings['id'] == mapping_to_delete].iloc[0]
            
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"品牌门店: {mapping_info['brand_store_name']}")
                st.info(f"平台: {mapping_info['platform']}")
            with col2:
                st.info(f"平台门店: {mapping_info['platform_store_name']}")
                st.info(f"状态: {'启用' if mapping_info['is_active'] else '禁用'}")
            
            # 确认删除
            confirm = st.checkbox("我确认要删除此映射关系")
            
            if confirm:
                if st.button("确认删除", type="primary"):
                    success, message = delete_store_mapping(mapping_to_delete)
                    if success:
                        st.success(message)
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(message)


if __name__ == "__main__":
    main()