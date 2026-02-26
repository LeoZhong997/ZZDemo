"""
事件管理器单元测试
"""
import pytest
import os
import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from ai.events.event_manager import (
    EventManager,
    PRESET_EVENTS
)


class TestEventManager:
    """事件管理器测试类"""
    
    @pytest.fixture
    def temp_storage_path(self, tmp_path):
        """创建临时存储路径"""
        return str(tmp_path / "test_events.json")
    
    @pytest.fixture
    def manager(self, temp_storage_path):
        """创建事件管理器实例"""
        return EventManager(events_file=temp_storage_path)
    
    @pytest.fixture
    def sample_event_data(self):
        """创建示例事件数据"""
        return {
            'date_str': '2026-01-15',
            'store_name': '测试门店',
            'event_type': 'promotion',
            'description': '开启新活动'
        }
    
    def test_manager_initialization(self, manager):
        """测试管理器初始化"""
        assert manager.events is not None
        assert isinstance(manager.events, dict)
    
    def test_add_event_basic(self, manager, sample_event_data):
        """测试基本事件添加"""
        result = manager.add_event(**sample_event_data)
        
        assert result.get('success') is True
        assert 'event' in result
        assert result['event']['description'] == sample_event_data['description']
    
    def test_add_event_with_id(self, manager, sample_event_data):
        """测试事件添加时自动生成ID"""
        result = manager.add_event(**sample_event_data)
        
        assert result.get('success') is True
        event = result.get('event', {})
        assert 'id' in event
        assert event['id'] is not None
    
    def test_add_event_with_timestamp(self, manager, sample_event_data):
        """测试事件添加时记录时间戳"""
        result = manager.add_event(**sample_event_data)
        
        assert result.get('success') is True
        event = result.get('event', {})
        assert 'created_at' in event
    
    def test_get_events_all(self, manager, sample_event_data):
        """测试获取所有事件"""
        # 添加几个事件
        manager.add_event(**sample_event_data)
        manager.add_event(**{**sample_event_data, 'date_str': '2026-01-16'})
        
        events = manager.get_events()
        assert len(events) >= 2
    
    def test_get_events_by_date_range(self, manager, sample_event_data):
        """测试按日期范围获取事件"""
        # 添加不同日期的事件
        manager.add_event(**sample_event_data)  # 2026-01-15
        manager.add_event(**{**sample_event_data, 'date_str': '2026-01-20'})
        manager.add_event(**{**sample_event_data, 'date_str': '2026-01-25'})
        
        # 获取 2026-01-14 到 2026-01-21 之间的事件
        events = manager.get_events('2026-01-14', '2026-01-21')
        
        # 应该只有 2026-01-15 和 2026-01-20 的事件
        dates = [e['date'] for e in events]
        assert '2026-01-15' in dates
        assert '2026-01-20' in dates
        assert '2026-01-25' not in dates
    
    def test_get_events_by_store(self, manager, sample_event_data):
        """测试按门店获取事件"""
        # 添加不同门店的事件
        manager.add_event(**sample_event_data)  # 测试门店
        manager.add_event(**{**sample_event_data, 'store_name': '其他门店'})
        
        events = manager.get_events(store_name='测试门店')
        
        # 应该只包含测试门店的事件
        for e in events:
            assert e['store_name'] in ['测试门店', '全局']
    
    def test_get_events_by_type(self, manager, sample_event_data):
        """测试按类型获取事件"""
        # 添加不同类型的事件
        manager.add_event(**sample_event_data)  # promotion
        manager.add_event(**{**sample_event_data, 'event_type': 'operation'})
        
        events = manager.get_events(event_type='promotion')
        
        assert all(e['event_type'] == 'promotion' for e in events)
    
    def test_delete_event(self, manager, sample_event_data):
        """测试删除事件"""
        # 添加事件
        result = manager.add_event(**sample_event_data)
        event_id = result['event']['id']
        
        # 删除事件
        delete_result = manager.delete_event(event_id)
        assert delete_result.get('success') is True
        
        # 确认已删除
        events = manager.get_events()
        assert not any(e['id'] == event_id for e in events)
    
    def test_delete_nonexistent_event(self, manager):
        """测试删除不存在的事件"""
        result = manager.delete_event('nonexistent_id')
        assert result.get('success') is False
    
    def test_update_event(self, manager, sample_event_data):
        """测试更新事件"""
        # 添加事件
        result = manager.add_event(**sample_event_data)
        event_id = result['event']['id']
        
        # 更新事件
        new_description = '更新后的描述'
        update_result = manager.update_event(event_id, {'description': new_description})
        
        assert update_result.get('success') is True
        assert update_result['event']['description'] == new_description
    
    def test_clear_events(self, manager, sample_event_data):
        """测试清空事件"""
        # 添加几个事件
        manager.add_event(**sample_event_data)
        manager.add_event(**{**sample_event_data, 'date_str': '2026-01-16'})
        
        # 清空
        manager.clear_events()
        
        events = manager.get_events()
        assert len(events) == 0
    
    def test_persistence(self, temp_storage_path, sample_event_data):
        """测试事件持久化"""
        # 创建管理器并添加事件
        manager1 = EventManager(events_file=temp_storage_path)
        manager1.add_event(**sample_event_data)
        
        # 创建新管理器，应该加载已保存的事件
        manager2 = EventManager(events_file=temp_storage_path)
        events = manager2.get_events()
        
        assert len(events) > 0
        assert events[0]['description'] == sample_event_data['description']
    
    def test_get_events_for_diagnosis(self, manager, sample_event_data):
        """测试获取用于诊断的事件"""
        # 添加事件
        manager.add_event(**sample_event_data)
        
        # 获取诊断用事件
        diagnosis_events = manager.get_events_for_diagnosis(
            start_date='2026-01-14',
            end_date='2026-01-16'
        )
        
        assert isinstance(diagnosis_events, list)
    
    def test_format_events_for_prompt(self, manager, sample_event_data):
        """测试格式化事件用于 Prompt"""
        # 添加事件
        manager.add_event(**sample_event_data)
        
        formatted = manager.format_events_for_prompt(
            start_date='2026-01-14',
            end_date='2026-01-16'
        )
        
        assert isinstance(formatted, str)
        assert len(formatted) > 0
    
    def test_get_summary(self, manager, sample_event_data):
        """测试获取事件摘要"""
        manager.add_event(**sample_event_data)
        
        summary = manager.get_summary()
        
        assert 'total_events' in summary
        assert 'by_type' in summary


class TestPresetEvents:
    """预设事件测试"""
    
    def test_preset_events_structure(self):
        """测试预设事件结构"""
        assert len(PRESET_EVENTS) > 0
        
        for event_type, config in PRESET_EVENTS.items():
            assert 'name' in config
            assert 'options' in config
            assert isinstance(config['options'], list)
    
    def test_common_event_types(self):
        """测试常见事件类型"""
        expected_types = ['promotion', 'operation', 'external', 'issue', 'positive']
        
        for event_type in expected_types:
            assert event_type in PRESET_EVENTS, f"缺少事件类型: {event_type}"


class TestEventValidation:
    """事件验证测试"""
    
    @pytest.fixture
    def manager(self, tmp_path):
        """创建管理器实例"""
        return EventManager(events_file=str(tmp_path / "test.json"))
    
    def test_valid_event(self, manager):
        """测试有效事件"""
        result = manager.add_event(
            date_str='2026-01-15',
            event_type='promotion',
            description='新活动'
        )
        
        assert result.get('success') is True
    
    def test_event_with_store(self, manager):
        """测试带门店的事件"""
        result = manager.add_event(
            date_str='2026-01-15',
            store_name='测试门店',
            event_type='promotion',
            description='新活动'
        )
        
        assert result.get('success') is True
        assert result['event']['store_name'] == '测试门店'
    
    def test_event_without_description(self, manager):
        """测试无描述的事件"""
        result = manager.add_event(
            date_str='2026-01-15',
            event_type='promotion',
            description=None
        )
        
        # 无描述应该失败
        assert result.get('success') is False


class TestEdgeCases:
    """边界情况测试"""
    
    @pytest.fixture
    def manager(self, tmp_path):
        """创建管理器实例"""
        return EventManager(events_file=str(tmp_path / "test.json"))
    
    def test_empty_description(self):
        """测试空描述"""
        pass  # 根据 add_event 实现调整
    
    def test_special_characters_in_description(self, tmp_path):
        """测试描述中的特殊字符"""
        manager = EventManager(events_file=str(tmp_path / "test.json"))
        
        result = manager.add_event(
            date_str='2026-01-15',
            event_type='promotion',
            description='特殊字符: <>&"\'测试'
        )
        
        assert result.get('success') is True
        assert '特殊字符' in result['event']['description']
    
    def test_long_description(self, tmp_path):
        """测试长描述"""
        manager = EventManager(events_file=str(tmp_path / "test.json"))
        long_desc = 'a' * 500  # 500 字符
        
        result = manager.add_event(
            date_str='2026-01-15',
            event_type='promotion',
            description=long_desc
        )
        
        assert result.get('success') is True
    
    def test_many_events(self, tmp_path):
        """测试大量事件"""
        manager = EventManager(events_file=str(tmp_path / "test.json"))
        
        for i in range(50):
            manager.add_event(
                date_str=f'2026-01-{(i % 28) + 1:02d}',
                event_type='promotion',
                description=f'事件 {i}'
            )
        
        events = manager.get_events()
        assert len(events) == 50


if __name__ == '__main__':
    pytest.main([__file__, '-v'])