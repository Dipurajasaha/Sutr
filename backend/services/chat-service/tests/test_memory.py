import pytest
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from app.services.memory_service import get_chat_history, update_chat_history, _chat_histories


def test_memory_initialization():
    """Test that new session initializes with SystemMessage."""
    _chat_histories.clear()
    
    history = get_chat_history("session_1")
    assert len(history) == 1
    assert history[0].type == "system"
    assert isinstance(history[0], SystemMessage)


def test_memory_update_and_limit():
    """Test that memory respects 21-message limit (1 system + 20 user-AI pairs)."""
    _chat_histories.clear()
    session_id = "session_limit_test"

    # Add 12 exchanges (24 messages: 12 Human, 12 AI)
    for i in range(12):
        update_chat_history(session_id, f"Human {i}", f"AI {i}")

    history = get_chat_history(session_id)

    # Total should be: 1 System prompt + last 20 messages (10 pairs) = 21 max
    assert len(history) == 21
    assert history[0].type == "system"
    # The oldest messages (Human 0, AI 0, Human 1, AI 1) should be sliced off
    assert history[1].content == "Human 2"
    assert history[-1].content == "AI 11"


def test_memory_single_exchange():
    """Test adding a single human-AI exchange."""
    _chat_histories.clear()
    session_id = "session_single"
    
    history = get_chat_history(session_id)
    assert len(history) == 1
    
    update_chat_history(session_id, "Hello", "Hi there!")
    history = get_chat_history(session_id)
    
    assert len(history) == 3  # System + Human + AI
    assert history[1].content == "Hello"
    assert history[2].content == "Hi there!"


def test_memory_multiple_sessions_isolated():
    """Test that different sessions maintain separate histories."""
    _chat_histories.clear()
    session_a = "session_a"
    session_b = "session_b"
    
    get_chat_history(session_a)
    get_chat_history(session_b)
    
    update_chat_history(session_a, "QA", "AA")
    update_chat_history(session_b, "QB", "AB")
    
    history_a = get_chat_history(session_a)
    history_b = get_chat_history(session_b)
    
    # Session A should have QA/AA
    contents_a = [m.content for m in history_a]
    assert "QA" in contents_a
    assert "AA" in contents_a
    assert "QB" not in contents_a
    assert "AB" not in contents_a
    
    # Session B should have QB/AB
    contents_b = [m.content for m in history_b]
    assert "QB" in contents_b
    assert "AB" in contents_b
    assert "QA" not in contents_b
    assert "AA" not in contents_b


def test_memory_exactly_at_limit():
    """Test that history at exactly 21 messages doesn't slice until next update."""
    _chat_histories.clear()
    session_id = "session_at_limit"
    
    get_chat_history(session_id)
    
    # Add exactly 10 exchanges (21 total messages)
    for i in range(10):
        update_chat_history(session_id, f"Q{i}", f"A{i}")
    
    history = get_chat_history(session_id)
    assert len(history) == 21
    
    # Add one more
    update_chat_history(session_id, "Q10", "A10")
    history = get_chat_history(session_id)
    
    assert len(history) == 21
    assert "Q0" not in [m.content for m in history]  # First Q removed
    assert "A0" not in [m.content for m in history]  # First A removed
    assert "Q10" in [m.content for m in history]  # New Q added


def test_memory_system_message_preserved():
    """Test that system message is always preserved."""
    _chat_histories.clear()
    session_id = "session_preserve_system"
    
    history1 = get_chat_history(session_id)
    system_msg = history1[0]
    
    # Add many exchanges
    for i in range(20):
        update_chat_history(session_id, f"Q{i}", f"A{i}")
    
    history_final = get_chat_history(session_id)
    assert history_final[0] == system_msg
    assert len(history_final) == 21


def test_memory_message_types():
    """Test that messages are correct types (HumanMessage and AIMessage)."""
    _chat_histories.clear()
    session_id = "session_types"
    
    get_chat_history(session_id)
    update_chat_history(session_id, "User query", "AI response")
    
    history = get_chat_history(session_id)
    assert isinstance(history[0], SystemMessage)
    assert isinstance(history[1], HumanMessage)
    assert isinstance(history[2], AIMessage)


def test_memory_exact_content_preservation():
    """Test that message content is preserved exactly as provided."""
    _chat_histories.clear()
    session_id = "session_content"
    
    get_chat_history(session_id)
    
    test_query = "This is a complex query with special chars: !@#$%^&*()"
    test_response = "Response with\nmultiple\nlines and symbols: <>&"
    
    update_chat_history(session_id, test_query, test_response)
    history = get_chat_history(session_id)
    
    assert history[1].content == test_query
    assert history[2].content == test_response


def test_memory_sequential_access():
    """Test accessing history multiple times without modification."""
    _chat_histories.clear()
    session_id = "session_sequential"
    
    get_chat_history(session_id)
    update_chat_history(session_id, "Q1", "A1")
    
    # Access history multiple times
    history1 = get_chat_history(session_id)
    history2 = get_chat_history(session_id)
    history3 = get_chat_history(session_id)
    
    # Should all be identical
    assert len(history1) == len(history2) == len(history3) == 3
    assert history1[1].content == history2[1].content == history3[1].content == "Q1"


def test_memory_persists_after_cache_clear():
    """Test that history survives in-memory cache clearing via the persistent store."""
    _chat_histories.clear()
    session_id = "session_persistent"

    get_chat_history(session_id)
    update_chat_history(session_id, "What is stemming?", "Stemming reduces words to roots.")

    _chat_histories.clear()
    history = get_chat_history(session_id)

    contents = [message.content for message in history]
    assert "What is stemming?" in contents
    assert "Stemming reduces words to roots." in contents