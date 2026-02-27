"""
QA Engine 单元测试
测试智能问答引擎核心功能
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from ai.engines.qa_engine import QAEngine, ask_question, quick_analysis


# ========== Fixtures ==========
@pytest.fixture
def mock_llm_adapter():
    """Mock LLM 适配器"""
    adapter = Mock()
    adapter.chat.return_value = "这是 AI 的模拟回复"
    adapter.stream_chat.return_value = iter(["这是", " AI", " 的", "模拟", "回复"])
    adapter.test_connection.return_value = {"success": True, "latency_ms": 100}
    return adapter


@pytest.fixture
def sample_df():
    """创建测试数据"""
    np.random.seed(42)
    dates = pd.date_range(start='2026-01-01', periods=7, freq='D')
    
    data = []
    for date in dates:
        for store in ['门店A', '门店B', '门店C']:
            for platform in ['美团', '饿了么']:
                data.append({
                    'order_date': date,
                    'brand_store_name': store,
                    'platform': platform,
                    'actual_income': np.random.uniform(500, 2000),
                    'valid_order_count': np.random.randint(20, 100),
                    'platform_revenue': np.random.uniform(600, 2500),
                    'exposure_count': np.random.randint(1000, 5000),
                    'entry_count': np.random.randint(100, 500),
                    'margin_rate': np.random.uniform(0.6, 0.85),
                    'competitor_rank': np.random.randint(1, 20)
                })
    
    return pd.DataFrame(data)


@pytest.fixture
def qa_engine(mock_llm_adapter):
    """创建 QA Engine 实例"""
    return QAEngine(llm_adapter=mock_llm_adapter, session_id="test_session")


# ========== 基础功能测试 ==========
class TestQAEngineInit:
    """QA Engine 初始化测试"""
    
    def test_init_with_adapter(self, mock_llm_adapter):
        """测试使用适配器初始化"""
        engine = QAEngine(llm_adapter=mock_llm_adapter)
        assert engine.llm_adapter is mock_llm_adapter
        assert engine.session_id == "default"
    
    def test_init_with_session_id(self, mock_llm_adapter):
        """测试使用 session_id 初始化"""
        engine = QAEngine(llm_adapter=mock_llm_adapter, session_id="custom_session")
        assert engine.session_id == "custom_session"
    
    def test_init_data_context_empty(self, qa_engine):
        """测试初始数据上下文为空"""
        assert qa_engine._data_context == {}
        assert qa_engine._current_df is None


class TestSetDataContext:
    """设置数据上下文测试"""
    
    def test_set_data_context_success(self, qa_engine, sample_df):
        """测试成功设置数据上下文"""
        result = qa_engine.set_data_context(sample_df)
        
        assert result["success"] is True
        assert result["record_count"] == len(sample_df)
        assert "data_context" in result
        
        # 验证数据上下文内容
        ctx = result["data_context"]
        assert "date_range" in ctx
        assert "revenue" in ctx
        assert "orders" in ctx
        assert "store_count" in ctx
        assert "platforms" in ctx
    
    def test_set_data_context_empty_df(self, qa_engine):
        """测试空 DataFrame"""
        empty_df = pd.DataFrame()
        result = qa_engine.set_data_context(empty_df)
        
        assert result["success"] is False
        assert result["message"] == "数据为空"
    
    def test_set_data_context_stores_top5(self, qa_engine, sample_df):
        """测试门店排名"""
        qa_engine.set_data_context(sample_df)
        
        top_stores = qa_engine._data_context.get("top_stores", [])
        assert len(top_stores) <= 5
        assert all("name" in s and "revenue" in s for s in top_stores)
    
    def test_set_data_context_platforms(self, qa_engine, sample_df):
        """测试平台列表"""
        qa_engine.set_data_context(sample_df)
        
        platforms = qa_engine._data_context.get("platforms", [])
        assert "美团" in platforms
        assert "饿了么" in platforms


class TestAsk:
    """问答功能测试"""
    
    def test_ask_basic_question(self, qa_engine, sample_df):
        """测试基本问答"""
        qa_engine.set_data_context(sample_df)
        
        response = qa_engine.ask("本周表现如何？")
        
        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0
        qa_engine.llm_adapter.chat.assert_called_once()
    
    def test_ask_empty_question(self, qa_engine, sample_df):
        """测试空问题"""
        qa_engine.set_data_context(sample_df)
        
        response = qa_engine.ask("")
        assert "请输入" in response
        
        response = qa_engine.ask("   ")
        assert "请输入" in response
    
    def test_ask_no_data(self, qa_engine):
        """测试无数据时的问答"""
        response = qa_engine.ask("本周表现如何？")
        
        # 应该仍然返回响应，但可能提示数据不足
        assert response is not None
    
    def test_ask_records_conversation(self, qa_engine, sample_df):
        """测试问答记录对话历史"""
        qa_engine.set_data_context(sample_df)
        
        initial_history = qa_engine.get_conversation_history()
        qa_engine.ask("测试问题")
        
        new_history = qa_engine.get_conversation_history()
        assert len(new_history) > len(initial_history)
    
    def test_ask_with_history(self, qa_engine, sample_df):
        """测试多轮对话"""
        qa_engine.set_data_context(sample_df)
        
        # 第一轮
        qa_engine.ask("第一个问题")
        
        # 第二轮（包含历史）
        qa_engine.ask("第二个问题")
        
        history = qa_engine.get_conversation_history()
        assert len(history) >= 2
    
    def test_ask_without_history(self, qa_engine, sample_df):
        """测试不包含历史的问答"""
        qa_engine.set_data_context(sample_df)
        
        qa_engine.ask("第一个问题")
        qa_engine.ask("第二个问题", include_history=False)
        
        # 验证 LLM 被调用
        assert qa_engine.llm_adapter.chat.call_count == 2
    
    def test_ask_error_handling(self, qa_engine, sample_df):
        """测试错误处理"""
        qa_engine.set_data_context(sample_df)
        qa_engine.llm_adapter.chat.side_effect = Exception("API 错误")
        
        response = qa_engine.ask("测试问题")
        
        assert "错误" in response or "⚠️" in response


class TestStreamAsk:
    """流式问答测试"""
    
    def test_stream_ask_basic(self, qa_engine, sample_df):
        """测试流式问答"""
        qa_engine.set_data_context(sample_df)
        
        chunks = list(qa_engine.stream_ask("测试问题"))
        
        assert len(chunks) > 0
        full_response = ''.join(chunks)
        assert "模拟回复" in full_response
    
    def test_stream_ask_empty_question(self, qa_engine, sample_df):
        """测试流式问答空问题"""
        qa_engine.set_data_context(sample_df)
        
        chunks = list(qa_engine.stream_ask(""))
        assert "请输入" in chunks[0]
    
    def test_stream_ask_records_conversation(self, qa_engine, sample_df):
        """测试流式问答记录对话"""
        qa_engine.set_data_context(sample_df)
        
        list(qa_engine.stream_ask("测试问题"))
        
        history = qa_engine.get_conversation_history()
        assert len(history) > 0


class TestQuickQuestion:
    """快捷问题测试"""
    
    def test_quick_question_summary(self, qa_engine, sample_df):
        """测试总结类快捷问题"""
        qa_engine.set_data_context(sample_df)
        
        response = qa_engine.quick_question("summary")
        
        assert response is not None
        qa_engine.llm_adapter.chat.assert_called_once()
    
    def test_quick_question_best_store(self, qa_engine, sample_df):
        """测试门店分析快捷问题"""
        qa_engine.set_data_context(sample_df)
        
        response = qa_engine.quick_question("best_store")
        assert response is not None
    
    def test_quick_question_suggestions(self, qa_engine, sample_df):
        """测试建议类快捷问题"""
        qa_engine.set_data_context(sample_df)
        
        response = qa_engine.quick_question("suggestions")
        assert response is not None


class TestGetSuggestedQuestions:
    """建议问题测试"""
    
    def test_get_suggested_questions_basic(self, qa_engine):
        """测试基本建议问题"""
        questions = qa_engine.get_suggested_questions()
        
        assert len(questions) > 0
        assert all("label" in q and "type" in q for q in questions)
    
    def test_get_suggested_questions_with_data(self, qa_engine, sample_df):
        """测试有数据时的建议问题"""
        qa_engine.set_data_context(sample_df)
        
        questions = qa_engine.get_suggested_questions()
        
        # 应该包含基础问题
        question_types = [q["type"] for q in questions]
        assert "summary" in question_types
        assert "best_store" in question_types
    
    def test_get_suggested_questions_multi_platform(self, qa_engine, sample_df):
        """测试多平台时的建议问题"""
        qa_engine.set_data_context(sample_df)
        
        questions = qa_engine.get_suggested_questions()
        question_types = [q["type"] for q in questions]
        
        # 多平台应该有平台对比问题
        assert "platform_compare" in question_types


class TestClearContext:
    """清除上下文测试"""
    
    def test_clear_context(self, qa_engine, sample_df):
        """测试清除对话上下文"""
        qa_engine.set_data_context(sample_df)
        qa_engine.ask("测试问题")
        
        # 确保有对话历史
        assert len(qa_engine.get_conversation_history()) > 0
        
        # 清除
        qa_engine.clear_context()
        
        # 验证清除
        assert len(qa_engine.get_conversation_history()) == 0


class TestGetConversationHistory:
    """对话历史测试"""
    
    def test_get_conversation_history_empty(self, qa_engine):
        """测试空对话历史"""
        history = qa_engine.get_conversation_history()
        assert history == []
    
    def test_get_conversation_history_after_ask(self, qa_engine, sample_df):
        """测试问答后的对话历史"""
        qa_engine.set_data_context(sample_df)
        qa_engine.ask("问题1")
        qa_engine.ask("问题2")
        
        history = qa_engine.get_conversation_history()
        assert len(history) >= 2


class TestGetContextSummary:
    """上下文摘要测试"""
    
    def test_get_context_summary(self, qa_engine, sample_df):
        """测试获取上下文摘要"""
        qa_engine.set_data_context(sample_df)
        
        summary = qa_engine.get_context_summary()
        
        assert "session_id" in summary
        assert "context" in summary
        assert "data_loaded" in summary
        assert summary["data_loaded"] is True


class TestAskAboutStore:
    """门店问答测试"""
    
    def test_ask_about_store(self, qa_engine, sample_df):
        """测试询问特定门店"""
        qa_engine.set_data_context(sample_df)
        
        response = qa_engine.ask_about_store("门店A")
        
        assert response is not None
        qa_engine.llm_adapter.chat.assert_called()
    
    def test_ask_about_store_not_found(self, qa_engine, sample_df):
        """测试询问不存在的门店"""
        qa_engine.set_data_context(sample_df)
        
        response = qa_engine.ask_about_store("不存在的门店")
        
        assert "未找到" in response
    
    def test_ask_about_store_no_data(self, qa_engine):
        """测试无数据时的门店问答"""
        response = qa_engine.ask_about_store("门店A")
        
        assert "请先加载数据" in response


class TestCompareEntities:
    """对比分析测试"""
    
    def test_compare_stores(self, qa_engine, sample_df):
        """测试门店对比"""
        qa_engine.set_data_context(sample_df)
        
        response = qa_engine.compare_entities(
            "store", 
            ["门店A", "门店B"],
            "收入表现"
        )
        
        assert response is not None
    
    def test_compare_platforms(self, qa_engine, sample_df):
        """测试平台对比"""
        qa_engine.set_data_context(sample_df)
        
        response = qa_engine.compare_entities(
            "platform",
            ["美团", "饿了么"],
            "整体表现"
        )
        
        assert response is not None
    
    def test_compare_single_entity(self, qa_engine, sample_df):
        """测试单个实体对比"""
        qa_engine.set_data_context(sample_df)
        
        response = qa_engine.compare_entities("store", ["门店A"])
        
        assert "至少提供两个" in response
    
    def test_compare_no_data(self, qa_engine):
        """测试无数据时的对比"""
        response = qa_engine.compare_entities("store", ["门店A", "门店B"])
        
        assert "请先加载数据" in response


# ========== 便捷函数测试 ==========
class TestConvenienceFunctions:
    """便捷函数测试"""
    
    def test_ask_question(self, sample_df, mock_llm_adapter):
        """测试 ask_question 便捷函数"""
        with patch('ai.engines.qa_engine.get_llm_adapter', return_value=mock_llm_adapter):
            response = ask_question(sample_df, "测试问题", session_id="test")
            
            assert response is not None
    
    def test_quick_analysis(self, sample_df, mock_llm_adapter):
        """测试 quick_analysis 便捷函数"""
        with patch('ai.engines.qa_engine.get_llm_adapter', return_value=mock_llm_adapter):
            response = quick_analysis(sample_df, "summary", session_id="test")
            
            assert response is not None


# ========== 边界条件测试 ==========
class TestEdgeCases:
    """边界条件测试"""
    
    def test_very_long_question(self, qa_engine, sample_df):
        """测试超长问题"""
        qa_engine.set_data_context(sample_df)
        
        long_question = "这是一个很长的问题" * 100
        response = qa_engine.ask(long_question)
        
        assert response is not None
    
    def test_special_characters_in_question(self, qa_engine, sample_df):
        """测试特殊字符问题"""
        qa_engine.set_data_context(sample_df)
        
        special_question = "问题包含特殊字符: @#$%^&*()"
        response = qa_engine.ask(special_question)
        
        assert response is not None
    
    def test_multiline_question(self, qa_engine, sample_df):
        """测试多行问题"""
        qa_engine.set_data_context(sample_df)
        
        multiline = "这是第一行\n这是第二行\n这是第三行"
        response = qa_engine.ask(multiline)
        
        assert response is not None
    
    def test_single_row_data(self, qa_engine):
        """测试单行数据"""
        single_row_df = pd.DataFrame([{
            'order_date': pd.Timestamp('2026-01-01'),
            'brand_store_name': '门店A',
            'platform': '美团',
            'actual_income': 1000,
            'valid_order_count': 50,
            'platform_revenue': 1200,
            'exposure_count': 1000,
            'entry_count': 100,
            'margin_rate': 0.83
        }])
        
        result = qa_engine.set_data_context(single_row_df)
        
        assert result["success"] is True
        assert result["record_count"] == 1