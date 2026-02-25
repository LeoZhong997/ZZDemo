"""
直接更新数据库中的转化率值（从小数格式转换为百分比格式）
"""
from sqlalchemy import create_engine, text
from ..config import get_connection_string, TABLE_NAME

def main():
    print("\n" + "="*60)
    print("🔄 修复数据库中的转化率数据")
    print("="*60)
    
    engine = create_engine(get_connection_string(), echo=False)
    
    # 需要转换的转化率字段
    conversion_fields = [
        'store_entry_rate',
        'order_conversion_rate',
        'new_customer_entry_rate',
        'new_customer_order_rate',
        'old_customer_entry_rate',
        'old_customer_order_rate',
        'repurchase_rate',
        'five_min_reply_rate',
        'one_min_reply_rate',
        'message_reply_rate',
        'service_negative_feedback_rate',
        'food_safety_negative_feedback_rate',
        'meal_completion_report_rate',
        'merchant_cancellation_rate',
        'net_margin_rate',
        'real_net_margin_rate'
    ]
    
    # 更新每个字段
    for field in conversion_fields:
        print(f"\n📊 更新 {field}...")
        
        with engine.connect() as conn:
            # 先查看当前值
            check_query = text(f"""
                SELECT {field}, 
                       CASE 
                         WHEN {field} < 1 AND {field} > 0 THEN '小数格式'
                         WHEN {field} >= 1 AND {field} <= 100 THEN '百分比格式'
                         ELSE '异常值'
                       END as format_type
                FROM {TABLE_NAME}
                WHERE date BETWEEN '2026-01-11' AND '2026-01-18'
                LIMIT 5
            """)
            result = conn.execute(check_query)
            rows = result.fetchall()
            
            if len(rows) > 0:
                print(f"   当前值示例:")
                for row in rows:
                    if row[0] is not None:
                        print(f"      {row[0]:.4f}% ({row[1]})")
                    else:
                        print(f"      NULL ({row[1]})")
            
            # 执行更新（将小于1的正值乘以100）
            update_query = text(f"""
                UPDATE {TABLE_NAME}
                SET {field} = {field} * 100
                WHERE date BETWEEN '2026-01-11' AND '2026-01-18'
                  AND {field} < 1 
                  AND {field} > 0
            """)
            result = conn.execute(update_query)
            conn.commit()
            
            if result.rowcount > 0:
                print(f"   ✅ 更新了 {result.rowcount} 条记录")
            else:
                print(f"   ℹ️  无需更新（已经是正确格式）")
            
            # 验证更新后的值
            verify_query = text(f"""
                SELECT AVG({field}) as avg_value
                FROM {TABLE_NAME}
                WHERE date BETWEEN '2026-01-11' AND '2026-01-18'
            """)
            result = conn.execute(verify_query)
            avg_value = result.fetchone()[0]
            if avg_value is not None:
                print(f"   更新后平均值: {avg_value:.2f}%")
            else:
                print(f"   更新后平均值: NULL (字段为空)")
    
    print(f"\n{'='*60}")
    print(f"✅ 转化率修复完成！")
    print(f"{'='*60}")

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ 修复失败: {e}")
        import traceback
        traceback.print_exc()