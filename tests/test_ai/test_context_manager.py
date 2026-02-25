"""
上下文管理器单元测试
"""
import pytest
from ai.core.context_manager import ContextManager, SessionContextManager, get_context, get_session_manager


class TestContextManager:
    """ContextManager 测试类"""
    
    def setup_method(self):
        """每个测试方法前的初始化"""
        self.manager = ContextManager(max_turns=5)
    
    def test_init(self):
        """测试初始化"""
        assert self.manager is not None
        assert self.manager.max_turns == 5
    
    def test_add_turn(self):
        """测试添加对话轮次"""
        self.manager.add_turn("用户消息", "助手回复")
        
        history = self.manager.get_history()
        assert len(history) == 2  # user + assistant
    
    def test_add_multiple_turns(self):
        """测试添加多轮对话"""
        self.manager.add_turn("消息1", "回复1")
        self.manager.add_turn("消息2", "回复2")
        self.manager.add_turn("消息3", "回复3")
        
        history = self.manager.get_history()
        assert len(history) == 6  # 3轮 x 2条
    
    def test_max_turns_limit(self):
        """测试最大轮数限制"""
        manager = ContextManager(max_turns=2)
        
        manager.add_turn("消息1", "回复1")
        manager.add_turn("消息2", "回复2")
        manager.add_turn("消息3", "回复3")  # 应该踢掉最早的一轮
        
        history = manager.get_history()
        assert len(history) == 4  # 2轮 x 2条
    
    def test_clear(self):
        """测试清除历史"""
        self.manager.add_turn("消息", "回复")
        self.manager.clear()
        
        history = self.manager.get_history()
        assert len(history) == 0
    
    def test_get_last_n_turns(self):
        """测试获取最近n轮对话"""
        self.manager.add_turn("消息1", "回复1")
        self.manager.add_turn("消息2", "回复2")
        self.manager.add_turn("消息3", "回复3")
        
        last_turns = self.manager.get_last_n_turns(2)
        assert len(last_turns) == 4  # 2轮 x 2条
    
    def test_get_history_format(self):
        """测试历史记录格式"""
        self.manager.add_turn("你好", "你好！有什么可以帮助你的？")
        
        history = self.manager.get_history()
        assert isinstance(history, list)
        assert len(history) == 2
        
        # 检查消息格式
        user_msg = history[0]
        assert user_msg['role'] == 'user'
        assert user_msg['content'] == '你好'
        
        assistant_msg = history[1]
        assert assistant_msg['role'] == 'assistant'


class TestSessionContextManager:
    """SessionContextManager 测试类"""
    
    def test_init(self):
        """测试初始化"""
        manager = SessionContextManager()
        assert manager is not None
    
    def test_get_or_create(self):
        """测试获取或创建上下文"""
        context = manager.get_or_create("test_session")
        assert context is not None
        assert isinstance(context, ContextManager)
    
    def test_get_same_session(self):
        """测试同一 session 返回相同上下文"""
        context1 = manager.get_or_create("same_session")
        context2 = manager.get_or_create("same_session")
        
        assert context1 is context2
    
    def test_get_different_sessions(self):
        """测试不同 session 返回不同上下文"""
        context1 = manager.get_or_create("session_1")
        context2 = manager.get_or_create("session_2")
        
        assert context1 is not context2
    
    def test_clear_session(self):
        """测试清除 session"""
        manager.get_or_create("to_clear")
        manager.clear_session("to_clear")
        
        # 清除后应该是新的上下文
        context_after = manager.get_or_create("to_clear")
        assert context_after is not None


class TestConvenienceFunctions:
    """便捷函数测试"""
    
    def test_get_context(self):
        """测试 get_context 函数"""
        context = get_context("test_func_session")
        assert context is not None
        assert isinstance(context, ContextManager)
    
    def test_get_session_manager(self):
        """测试 get_session_manager 函数"""
        manager = get_session_manager()
        assert manager is not None
        assert isinstance(manager, SessionContextManager)
    
    def test_get_session_manager_singleton(self):
        """测试 get_session_manager 返回单例"""
        manager1 = get_session_manager()
        manager2 = get_session_manager()
        
        assert manager1 is manager2