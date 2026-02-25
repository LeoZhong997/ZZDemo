"""
对话上下文管理器
管理对话历史、限制上下文长度、清理过期上下文
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from ai.config import get_ai_config

logger = logging.getLogger(__name__)


class ContextManager:
    """
    对话上下文管理器
    
    功能：
    - 管理对话历史
    - 限制上下文长度
    - 清理过期上下文
    - 支持多轮对话
    """
    
    def __init__(self, max_turns: int = 10, max_tokens: int = 8000):
        """
        初始化上下文管理器
        
        Args:
            max_turns: 最大对话轮数
            max_tokens: 最大 token 数量（估算）
        """
        self.max_turns = max_turns
        self.max_tokens = max_tokens
        self._history: List[Dict[str, Any]] = []
        self._created_at = datetime.now()
        
        # 从配置读取参数
        config = get_ai_config('prompt', {})
        if config:
            self.max_tokens = config.get('max_context_length', max_tokens)
    
    def add_turn(self, user_message: str, assistant_message: str) -> None:
        """
        添加一轮对话
        
        Args:
            user_message: 用户消息
            assistant_message: 助手回复
        """
        turn = {
            "role": "conversation",
            "user": user_message,
            "assistant": assistant_message,
            "timestamp": datetime.now().isoformat()
        }
        
        self._history.append(turn)
        
        # 检查是否超出限制
        self._enforce_limits()
        
        logger.debug(f"添加对话轮次，当前共 {len(self._history)} 轮")
    
    def add_message(self, role: str, content: str) -> None:
        """
        添加单条消息
        
        Args:
            role: 消息角色 (user/assistant/system)
            content: 消息内容
        """
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        
        self._history.append(message)
        self._enforce_limits()
    
    def get_history(self) -> List[Dict]:
        """
        获取历史消息
        
        Returns:
            消息列表，格式兼容 LLM API
        """
        return self._format_for_llm()
    
    def get_raw_history(self) -> List[Dict[str, Any]]:
        """
        获取原始历史记录
        
        Returns:
            原始历史记录列表
        """
        return self._history.copy()
    
    def clear(self) -> None:
        """清除历史"""
        self._history = []
        self._created_at = datetime.now()
        logger.info("对话历史已清除")
    
    def get_last_n_turns(self, n: int) -> List[Dict]:
        """
        获取最近 n 轮对话
        
        Args:
            n: 轮数
            
        Returns:
            消息列表
        """
        # 获取最近的对话轮次
        conversations = [h for h in self._history if h.get('role') == 'conversation']
        recent = conversations[-n:] if n < len(conversations) else conversations
        
        # 格式化为 LLM 格式
        messages = []
        for turn in recent:
            messages.append({"role": "user", "content": turn["user"]})
            messages.append({"role": "assistant", "content": turn["assistant"]})
        
        return messages
    
    def get_context_summary(self) -> Dict[str, Any]:
        """
        获取上下文摘要
        
        Returns:
            上下文统计信息
        """
        user_messages = len([h for h in self._history if h.get('role') == 'user'])
        assistant_messages = len([h for h in self._history if h.get('role') == 'assistant'])
        conversations = len([h for h in self._history if h.get('role') == 'conversation'])
        
        # 估算 token 数量（粗略估计：1 token ≈ 1.5 中文字符）
        total_chars = sum(
            len(h.get('content', '')) + len(h.get('user', '')) + len(h.get('assistant', ''))
            for h in self._history
        )
        estimated_tokens = total_chars // 2
        
        return {
            "total_turns": len(self._history),
            "user_messages": user_messages,
            "assistant_messages": assistant_messages,
            "conversations": conversations,
            "estimated_tokens": estimated_tokens,
            "max_turns": self.max_turns,
            "max_tokens": self.max_tokens,
            "created_at": self._created_at.isoformat()
        }
    
    def build_messages(self, 
                       system_prompt: str,
                       current_question: str,
                       include_history: bool = True) -> List[Dict[str, str]]:
        """
        构建发送给 LLM 的消息列表
        
        Args:
            system_prompt: 系统提示词
            current_question: 当前问题
            include_history: 是否包含历史
            
        Returns:
            格式化的消息列表
        """
        messages = []
        
        # 添加系统提示词
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # 添加历史对话
        if include_history:
            history_messages = self._format_for_llm()
            messages.extend(history_messages)
        
        # 添加当前问题
        messages.append({"role": "user", "content": current_question})
        
        return messages
    
    def _format_for_llm(self) -> List[Dict[str, str]]:
        """
        格式化历史记录为 LLM API 格式
        
        Returns:
            格式化的消息列表
        """
        messages = []
        
        for item in self._history:
            if item.get('role') == 'conversation':
                # 对话轮次
                messages.append({"role": "user", "content": item["user"]})
                messages.append({"role": "assistant", "content": item["assistant"]})
            elif item.get('role') in ['user', 'assistant']:
                # 单条消息
                messages.append({"role": item["role"], "content": item["content"]})
        
        return messages
    
    def _enforce_limits(self) -> None:
        """执行限制（轮数和 token 数量）"""
        # 按轮数限制
        if len(self._history) > self.max_turns * 2:  # 每轮对话最多2条记录
            # 保留最近的对话
            self._history = self._history[-(self.max_turns * 2):]
            logger.info(f"对话历史已裁剪至 {len(self._history)} 条")
        
        # 按 token 数量限制（粗略估计）
        while self._estimate_tokens() > self.max_tokens and len(self._history) > 2:
            # 移除最早的消息
            self._history.pop(0)
            logger.info("对话历史因 token 限制已裁剪")
    
    def _estimate_tokens(self) -> int:
        """估算当前 token 数量"""
        total_chars = sum(
            len(h.get('content', '')) + len(h.get('user', '')) + len(h.get('assistant', ''))
            for h in self._history
        )
        # 粗略估计：中文约 2 字符/token，英文约 4 字符/token
        return total_chars // 2
    
    def __len__(self) -> int:
        """返回历史记录数量"""
        return len(self._history)
    
    def __repr__(self) -> str:
        return f"ContextManager(turns={len(self._history)}, max_turns={self.max_turns})"


class SessionContextManager:
    """
    会话级别的上下文管理器
    支持多个独立会话
    """
    
    def __init__(self, max_sessions: int = 10):
        """
        初始化会话管理器
        
        Args:
            max_sessions: 最大会话数
        """
        self.max_sessions = max_sessions
        self._sessions: Dict[str, ContextManager] = {}
    
    def get_session(self, session_id: str) -> ContextManager:
        """
        获取或创建会话
        
        Args:
            session_id: 会话 ID
            
        Returns:
            上下文管理器
        """
        if session_id not in self._sessions:
            # 如果超出限制，移除最旧的会话
            if len(self._sessions) >= self.max_sessions:
                oldest_id = next(iter(self._sessions))
                del self._sessions[oldest_id]
                logger.info(f"移除旧会话: {oldest_id}")
            
            self._sessions[session_id] = ContextManager()
            logger.info(f"创建新会话: {session_id}")
        
        return self._sessions[session_id]
    
    def clear_session(self, session_id: str) -> bool:
        """
        清除指定会话
        
        Args:
            session_id: 会话 ID
            
        Returns:
            是否成功
        """
        if session_id in self._sessions:
            self._sessions[session_id].clear()
            del self._sessions[session_id]
            logger.info(f"清除会话: {session_id}")
            return True
        return False
    
    def clear_all(self) -> None:
        """清除所有会话"""
        self._sessions.clear()
        logger.info("清除所有会话")
    
    def list_sessions(self) -> List[str]:
        """列出所有会话 ID"""
        return list(self._sessions.keys())
    
    def get_session_stats(self) -> Dict[str, Any]:
        """获取会话统计"""
        return {
            "total_sessions": len(self._sessions),
            "max_sessions": self.max_sessions,
            "sessions": {
                sid: ctx.get_context_summary()
                for sid, ctx in self._sessions.items()
            }
        }


# 全局会话管理器实例
_global_session_manager: Optional[SessionContextManager] = None


def get_session_manager() -> SessionContextManager:
    """
    获取全局会话管理器实例
    
    Returns:
        SessionContextManager 实例
    """
    global _global_session_manager
    if _global_session_manager is None:
        _global_session_manager = SessionContextManager()
    return _global_session_manager


def get_context(session_id: str = "default") -> ContextManager:
    """
    获取指定会话的上下文管理器
    
    Args:
        session_id: 会话 ID
        
    Returns:
        ContextManager 实例
    """
    return get_session_manager().get_session(session_id)