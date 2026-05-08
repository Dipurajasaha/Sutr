"""Additional tests to close coverage gaps in agent_service and memory_service."""
import pytest
from unittest.mock import patch, MagicMock
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from app.services.agent_service import (
    build_contextual_query,
    _vector_search,
    _fetch_file_chunks,
    _store_sources,
    fetch_document_context,
)
from app.services.memory_service import (
    get_chat_history,
    update_chat_history,
    get_chat_history_records,
    _message_to_record,
    _record_to_message,
    _chat_histories,
)


class Test_BuildContextualQuery:
    """Test query building with conversation history."""

    def test_build_contextual_query_with_empty_history(self):
        """Empty history should return just the query."""
        result = build_contextual_query([], "What is this?")
        assert result == "What is this?"

    def test_build_contextual_query_with_history(self):
        """History should be included in query."""
        history = [
            HumanMessage(content="Hello"),
            AIMessage(content="Hi there"),
            HumanMessage(content="Tell me more"),
        ]
        result = build_contextual_query(history, "What is this?", max_turns=4)
        assert "User:" in result
        assert "Assistant:" in result
        assert "Current question:" in result
        assert "What is this?" in result

    def test_build_contextual_query_max_turns_limit(self):
        """Should limit history to max_turns."""
        history = [
            HumanMessage(content="Q1"),
            AIMessage(content="A1"),
            HumanMessage(content="Q2"),
            AIMessage(content="A2"),
            HumanMessage(content="Q3"),
            AIMessage(content="A3"),
        ]
        result = build_contextual_query(history, "Q4", max_turns=2)
        # Should only have 2 turns (4 messages): Q2, A2, Q3, A3
        assert result.count("User:") <= 2
        assert "Q1" not in result  # Oldest turn should be excluded


class Test_VectorSearch:
    """Test direct vector search function."""

    def test_vector_search_success(self):
        """Successful vector search returns results."""
        with patch("app.services.agent_service.httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value.__enter__.return_value = mock_client
            mock_response = MagicMock()
            mock_response.json.return_value = [
                {"chunk_id": "1", "text": "Result 1", "score": 0.9}
            ]
            mock_client.post.return_value = mock_response

            result = _vector_search("query text", "file-id")

            assert len(result) == 1
            assert result[0]["text"] == "Result 1"

    def test_vector_search_empty_results(self):
        """Empty vector search returns empty list."""
        with patch("app.services.agent_service.httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value.__enter__.return_value = mock_client
            mock_response = MagicMock()
            mock_response.json.return_value = []
            mock_client.post.return_value = mock_response

            result = _vector_search("query", "file-id")

            assert result == []


class Test_FetchFileChunks:
    """Test fallback chunk fetching."""

    def test_fetch_file_chunks_success(self):
        """Should fetch chunks from vector service."""
        with patch("app.services.agent_service.httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value.__enter__.return_value = mock_client
            mock_response = MagicMock()
            mock_response.json.return_value = [
                {"chunk_id": "c1", "text": "Chunk 1"}
            ]
            mock_client.get.return_value = mock_response

            result = _fetch_file_chunks("file-id", limit=4)

            assert len(result) == 1
            assert result[0]["text"] == "Chunk 1"


class Test_StoreSources:
    """Test source caching."""

    def test_store_sources_formats_correctly(self):
        """Should format data and cache it."""
        data = [
            {"chunk_id": "id1", "text": "Text 1", "start_time": 0.0, "end_time": 1.0},
            {"chunk_id": "id2", "text": "Text 2", "start_time": 1.0, "end_time": 2.0},
        ]
        result = _store_sources(data)

        assert "Context:" in result
        assert "Text 1" in result
        assert "Text 2" in result


class Test_FetchDocumentContext:
    """Test fetch_document_context fallback logic."""

    def test_fetch_document_context_with_results(self):
        """Should return formatted context when results found."""
        with patch("app.services.agent_service._vector_search") as mock_search:
            mock_search.return_value = [
                {"chunk_id": "c1", "text": "Context text"}
            ]

            result = fetch_document_context("query", "file-id")

            assert "Context:" in result
            assert "Context text" in result

    def test_fetch_document_context_fallback_to_chunks(self):
        """Should fallback to chunks if search returns empty."""
        with patch(
            "app.services.agent_service._vector_search"
        ) as mock_search, patch(
            "app.services.agent_service._fetch_file_chunks"
        ) as mock_chunks:
            mock_search.return_value = []
            mock_chunks.return_value = [{"chunk_id": "c1", "text": "Fallback text"}]

            result = fetch_document_context("query", "file-id")

            assert "Fallback text" in result
            mock_chunks.assert_called_once()

    def test_fetch_document_context_no_results(self):
        """Should return message when no context found."""
        with patch(
            "app.services.agent_service._vector_search"
        ) as mock_search, patch(
            "app.services.agent_service._fetch_file_chunks"
        ) as mock_chunks:
            mock_search.return_value = []
            mock_chunks.return_value = []

            result = fetch_document_context("query", "file-id")

            assert "No relevant information" in result

    def test_fetch_document_context_search_error(self):
        """Should handle search errors gracefully."""
        with patch(
            "app.services.agent_service._vector_search"
        ) as mock_search:
            mock_search.side_effect = Exception("Network error")

            result = fetch_document_context("query", "file-id")

            assert "Database search failed" in result


class Test_MessageConversion:
    """Test message to/from record conversion."""

    def test_message_to_record_human(self):
        """HumanMessage converts to record."""
        msg = HumanMessage(content="Hello")
        record = _message_to_record(msg)
        assert record["role"] == "human"
        assert record["content"] == "Hello"

    def test_message_to_record_ai(self):
        """AIMessage converts to record."""
        msg = AIMessage(content="Response")
        record = _message_to_record(msg)
        assert record["role"] == "ai"
        assert record["content"] == "Response"

    def test_message_to_record_system(self):
        """SystemMessage returns None."""
        msg = SystemMessage(content="System")
        record = _message_to_record(msg)
        assert record is None

    def test_record_to_message_human(self):
        """Record converts back to HumanMessage."""
        record = {"role": "human", "content": "User input"}
        msg = _record_to_message(record)
        assert isinstance(msg, HumanMessage)
        assert msg.content == "User input"

    def test_record_to_message_ai(self):
        """Record converts back to AIMessage."""
        record = {"role": "ai", "content": "AI output"}
        msg = _record_to_message(record)
        assert isinstance(msg, AIMessage)
        assert msg.content == "AI output"

    def test_record_to_message_unknown(self):
        """Unknown role returns None."""
        record = {"role": "unknown", "content": "Data"}
        msg = _record_to_message(record)
        assert msg is None


class Test_ChatHistory:
    """Test chat history management."""

    def test_get_chat_history_records(self):
        """Should return records without system message."""
        _chat_histories.clear()
        update_chat_history("session_1", "Hi", "Hello")
        update_chat_history("session_1", "How are you?", "I'm good")

        records = get_chat_history_records("session_1")

        assert len(records) == 4  # 2 human, 2 ai
        assert records[0]["role"] == "human"
        assert records[1]["role"] == "ai"

    def test_update_chat_history_rolling_window(self):
        """Should enforce 21-message limit."""
        _chat_histories.clear()
        for i in range(15):
            update_chat_history("session_2", f"Q{i}", f"A{i}")

        history = get_chat_history("session_2")

        # Should have system message (1) + last 20 messages
        assert len(history) <= 21
        # Oldest exchanges should be dropped
        assert "Q0" not in str(history[1:])
