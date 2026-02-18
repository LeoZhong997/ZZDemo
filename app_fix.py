            history_html = f'''
            <div style="background: #f8f9fa; padding: 16px 18px; border-radius: 8px; border: 1px solid #e0e0e0; height: 100%; min-height: 130px;">
                <div style="font-size: 13px; font-weight: bold; color: #1a1a1a; margin-bottom: 12px; border-bottom: 1px solid #d1d5db; padding-bottom: 8px;">历史到手率</div>
                <div style="font-size: 13px; color: #666666; margin-bottom: 6px;">上周: <span style="font-weight: 600; color: #1a1a1a;">{last_week_rate:.2f}%</span></div>
                <div style="font-size: 13px; color: #666666;">上上周: <span style="font-weight: 600; color: #1a1a1a;">{two_weeks_ago_rate:.2f}%</span></div>
            </div>
            '''
