"""
事件管理器
管理特殊事件和备注（如活动、天气、平台调整等）
"""
import json
import os
from datetime import datetime, date
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


# 预设事件类型
PRESET_EVENTS = {
    'promotion': {
        'name': '促销活动',
        'options': [
            '恢复神会员',
            '开启新活动',
            '调整满减',
            '新品上线',
            '更换包装',
            '限时折扣',
            '满减升级',
            '配送费调整'
        ]
    },
    'operation': {
        'name': '运营调整',
        'options': [
            '人员调整',
            '设备更换',
            '系统升级',
            '营业时间调整',
            '配送范围调整',
            '菜单调整'
        ]
    },
    'external': {
        'name': '外部因素',
        'options': [
            '恶劣天气',
            '平台调整',
            '竞对动作',
            '周边施工',
            '节假日',
            '特殊事件'
        ]
    },
    'issue': {
        'name': '问题事件',
        'options': [
            '食安投诉',
            '骑手纠纷',
            '顾客投诉',
            '设备故障',
            '原材料问题',
            '出餐延迟'
        ]
    },
    'positive': {
        'name': '正面事件',
        'options': [
            '好评增加',
            '排名提升',
            '流量上涨',
            '活动效果显著',
            '新客增长'
        ]
    }
}

# 默认事件存储路径
DEFAULT_EVENTS_FILE = 'config/events.json'


class EventManager:
    """
    事件管理器
    
    功能：
    - 添加/删除/修改事件
    - 按日期/门店查询事件
    - 格式化事件用于 Prompt
    - 持久化存储
    """
    
    def __init__(self, events_file: str = None):
        """
        初始化事件管理器
        
        Args:
            events_file: 事件存储文件路径
        """
        self.events_file = events_file or DEFAULT_EVENTS_FILE
        self.events = self._load_events()
    
    def add_event(self,
                  store_name: str = None,
                  date_str: str = None,
                  event_type: str = None,
                  description: str = None,
                  custom_data: Dict = None) -> Dict[str, Any]:
        """
        添加事件
        
        Args:
            store_name: 门店名称（None 表示全局事件）
            date_str: 日期字符串 (YYYY-MM-DD)
            event_type: 事件类型（promotion/operation/external/issue/positive）
            description: 事件描述
            custom_data: 自定义数据
            
        Returns:
            操作结果
        """
        if not date_str:
            date_str = datetime.now().strftime('%Y-%m-%d')
        
        if not description:
            return {'success': False, 'error': '事件描述不能为空'}
        
        event = {
            'id': self._generate_id(),
            'store_name': store_name or '全局',
            'date': date_str,
            'event_type': event_type or 'custom',
            'description': description,
            'created_at': datetime.now().isoformat(),
            'custom_data': custom_data or {}
        }
        
        # 按日期存储
        if date_str not in self.events:
            self.events[date_str] = []
        
        self.events[date_str].append(event)
        
        # 保存
        self._save_events()
        
        logger.info(f"添加事件: {event['id']} - {description}")
        
        return {
            'success': True,
            'event': event,
            'message': '事件添加成功'
        }
    
    def add_batch_events(self, events_list: List[Dict]) -> Dict[str, Any]:
        """
        批量添加事件
        
        Args:
            events_list: 事件列表
            
        Returns:
            操作结果
        """
        added_count = 0
        errors = []
        
        for event_data in events_list:
            result = self.add_event(
                store_name=event_data.get('store_name'),
                date_str=event_data.get('date'),
                event_type=event_data.get('event_type'),
                description=event_data.get('description'),
                custom_data=event_data.get('custom_data')
            )
            
            if result['success']:
                added_count += 1
            else:
                errors.append(result['error'])
        
        return {
            'success': added_count > 0,
            'added_count': added_count,
            'total': len(events_list),
            'errors': errors
        }
    
    def delete_event(self, event_id: str) -> Dict[str, Any]:
        """
        删除事件
        
        Args:
            event_id: 事件ID
            
        Returns:
            操作结果
        """
        for date_str, events in self.events.items():
            for i, event in enumerate(events):
                if event['id'] == event_id:
                    deleted = events.pop(i)
                    self._save_events()
                    logger.info(f"删除事件: {event_id}")
                    return {
                        'success': True,
                        'deleted_event': deleted,
                        'message': '事件删除成功'
                    }
        
        return {
            'success': False,
            'error': f'未找到事件: {event_id}'
        }
    
    def update_event(self, event_id: str, updates: Dict) -> Dict[str, Any]:
        """
        更新事件
        
        Args:
            event_id: 事件ID
            updates: 更新内容
            
        Returns:
            操作结果
        """
        for date_str, events in self.events.items():
            for event in events:
                if event['id'] == event_id:
                    # 更新字段
                    for key, value in updates.items():
                        if key != 'id':  # 不允许修改ID
                            event[key] = value
                    
                    event['updated_at'] = datetime.now().isoformat()
                    self._save_events()
                    
                    return {
                        'success': True,
                        'event': event,
                        'message': '事件更新成功'
                    }
        
        return {
            'success': False,
            'error': f'未找到事件: {event_id}'
        }
    
    def get_events(self,
                   start_date: str = None,
                   end_date: str = None,
                   store_name: str = None,
                   event_type: str = None) -> List[Dict]:
        """
        获取事件列表
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            store_name: 门店名称
            event_type: 事件类型
            
        Returns:
            事件列表
        """
        results = []
        
        for date_str, events in self.events.items():
            # 日期过滤
            if start_date and date_str < start_date:
                continue
            if end_date and date_str > end_date:
                continue
            
            for event in events:
                # 门店过滤
                if store_name and event.get('store_name') != store_name:
                    # 但保留全局事件
                    if event.get('store_name') != '全局':
                        continue
                
                # 类型过滤
                if event_type and event.get('event_type') != event_type:
                    continue
                
                results.append(event)
        
        # 按日期排序（最新的在前）
        results.sort(key=lambda x: x.get('date', ''), reverse=True)
        
        return results
    
    def get_events_by_date_range(self,
                                  start_date: str,
                                  end_date: str) -> Dict[str, List[Dict]]:
        """
        按日期范围获取事件（按日期分组）
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            按日期分组的事件字典
        """
        results = {}
        
        for date_str, events in self.events.items():
            if start_date <= date_str <= end_date:
                results[date_str] = events
        
        return results
    
    def get_events_for_diagnosis(self,
                                  start_date: str,
                                  end_date: str,
                                  store_names: List[str] = None) -> List[Dict]:
        """
        获取用于诊断报告的事件
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            store_names: 相关门店列表
            
        Returns:
            事件列表（包含全局事件和指定门店事件）
        """
        all_events = self.get_events(start_date, end_date)
        
        if store_names:
            # 过滤出全局事件或指定门店事件
            filtered = []
            for event in all_events:
                if event['store_name'] == '全局':
                    filtered.append(event)
                elif event['store_name'] in store_names:
                    filtered.append(event)
            return filtered
        
        return all_events
    
    def format_events_for_prompt(self,
                                  start_date: str,
                                  end_date: str,
                                  store_names: List[str] = None) -> str:
        """
        格式化事件用于 Prompt
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            store_names: 相关门店列表
            
        Returns:
            格式化的字符串
        """
        events = self.get_events_for_diagnosis(start_date, end_date, store_names)
        
        if not events:
            return "无特殊事件记录"
        
        lines = []
        
        # 按类型分组
        by_type = {}
        for event in events:
            etype = event.get('event_type', 'other')
            if etype not in by_type:
                by_type[etype] = []
            by_type[etype].append(event)
        
        # 类型名称映射
        type_names = {
            'promotion': '促销活动',
            'operation': '运营调整',
            'external': '外部因素',
            'issue': '问题事件',
            'positive': '正面事件',
            'custom': '自定义',
            'other': '其他'
        }
        
        for etype, type_events in by_type.items():
            type_name = type_names.get(etype, etype)
            lines.append(f"### {type_name}")
            
            for event in type_events:
                store = event.get('store_name', '')
                date_str = event.get('date', '')
                desc = event.get('description', '')
                
                if store == '全局':
                    lines.append(f"- [{date_str}] {desc}")
                else:
                    lines.append(f"- [{date_str}] **{store}**: {desc}")
            
            lines.append("")
        
        return '\n'.join(lines)
    
    def get_preset_options(self) -> Dict[str, Any]:
        """
        获取预设事件选项
        
        Returns:
            预设选项字典
        """
        return PRESET_EVENTS
    
    def clear_events(self, date_str: str = None) -> Dict[str, Any]:
        """
        清除事件
        
        Args:
            date_str: 指定日期，None 表示清除所有
            
        Returns:
            操作结果
        """
        if date_str:
            if date_str in self.events:
                count = len(self.events[date_str])
                del self.events[date_str]
                self._save_events()
                return {
                    'success': True,
                    'cleared_count': count,
                    'message': f'已清除 {date_str} 的 {count} 条事件'
                }
            else:
                return {
                    'success': False,
                    'error': f'未找到 {date_str} 的事件'
                }
        else:
            count = sum(len(events) for events in self.events.values())
            self.events = {}
            self._save_events()
            return {
                'success': True,
                'cleared_count': count,
                'message': f'已清除所有 {count} 条事件'
            }
    
    def get_summary(self) -> Dict[str, Any]:
        """
        获取事件摘要
        
        Returns:
            摘要信息
        """
        total_events = sum(len(events) for events in self.events.values())
        total_dates = len(self.events)
        
        # 按类型统计
        by_type = {}
        for events in self.events.values():
            for event in events:
                etype = event.get('event_type', 'other')
                by_type[etype] = by_type.get(etype, 0) + 1
        
        # 按门店统计
        by_store = {}
        for events in self.events.values():
            for event in events:
                store = event.get('store_name', '全局')
                by_store[store] = by_store.get(store, 0) + 1
        
        return {
            'total_events': total_events,
            'total_dates': total_dates,
            'by_type': by_type,
            'by_store': by_store,
            'date_range': {
                'earliest': min(self.events.keys()) if self.events else None,
                'latest': max(self.events.keys()) if self.events else None
            }
        }
    
    def _generate_id(self) -> str:
        """生成唯一事件ID"""
        import uuid
        return f"evt_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:6]}"
    
    def _load_events(self) -> Dict[str, List[Dict]]:
        """加载事件"""
        if os.path.exists(self.events_file):
            try:
                with open(self.events_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"加载事件文件失败: {e}")
                return {}
        return {}
    
    def _save_events(self) -> bool:
        """保存事件"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.events_file), exist_ok=True)
            
            with open(self.events_file, 'w', encoding='utf-8') as f:
                json.dump(self.events, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            logger.error(f"保存事件文件失败: {e}")
            return False


# 便捷函数
_event_manager = None

def get_event_manager() -> EventManager:
    """获取事件管理器单例"""
    global _event_manager
    if _event_manager is None:
        _event_manager = EventManager()
    return _event_manager


def add_event(store_name: str = None, date_str: str = None,
              event_type: str = None, description: str = None) -> Dict:
    """便捷函数：添加事件"""
    return get_event_manager().add_event(store_name, date_str, event_type, description)


def get_events(start_date: str = None, end_date: str = None,
               store_name: str = None) -> List[Dict]:
    """便捷函数：获取事件"""
    return get_event_manager().get_events(start_date, end_date, store_name)