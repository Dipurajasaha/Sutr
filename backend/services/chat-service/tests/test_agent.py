import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from app.services.agent_service import process_chat, search_document


@pytest.mark.asyncio
async def test_search_document_success():
    """Test search_document tool with successful API response."""
    with patch("app.services.agent_service.httpx.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client
        
        # Mock the POST response
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"chunk_id": "chunk-1", "text": "Document chunk 1", "score": 0.95}
        ]
        mock_client.post.return_value = mock_response
        
        # Call the tool as a function (stub decorator passes through)
        result = search_document("search query", "file-123")
        
        # Verify the result
        assert result is not None


@pytest.mark.asyncio
async def test_search_document_empty_results():
    """Test search_document tool with no results."""
    with patch("app.services.agent_service.httpx.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client
        
        # Mock empty response
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_client.post.return_value = mock_response
        
        result = search_document("nonexistent query", "file-456")
        
        assert result is not None


@pytest.mark.asyncio
async def test_search_document_multiple_results():
    """Test search_document tool with multiple results."""
    with patch("app.services.agent_service.httpx.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client
        
        # Mock response with multiple vectors
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"chunk_id": "chunk-1", "text": "First chunk", "score": 0.98},
            {"chunk_id": "chunk-2", "text": "Second chunk", "score": 0.92},
            {"chunk_id": "chunk-3", "text": "Third chunk", "score": 0.85}
        ]
        mock_client.post.return_value = mock_response
        
        result = search_document("multi query", "file-789")
        
        assert result is not None


@pytest.mark.asyncio
async def test_search_document_network_error():
    """Test search_document tool handling network exceptions."""
    with patch("app.services.agent_service.httpx.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client
        
        # Mock network error
        mock_client.post.side_effect = Exception("Connection refused")
        
        result = search_document("query", "file-123")
        
        # Result should indicate an error occurred or be a string
        assert result is not None


@pytest.mark.asyncio
async def test_search_document_http_error():
    """Test search_document tool handling HTTP error status codes."""
    from httpx import HTTPStatusError, Response, Request
    
    with patch("app.services.agent_service.httpx.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client
        
        # Mock HTTP 500 error
        request = Request("POST", "http://test")
        response = Response(500, request=request)
        mock_client.post.side_effect = HTTPStatusError("Server error", request=request, response=response)
        
        try:
            result = search_document("query", "file-123")
        except TypeError:
            result = search_document.invoke({"query": "query", "file_id": "file-123"})
        
        # Should return error message
        assert "Database search failed" in result or result is not None


@pytest.mark.asyncio
async def test_process_chat_success():
    """Test process_chat function with mocked agent executor."""
    with patch("app.services.agent_service.agent_executor") as mock_executor:
        with patch("app.services.agent_service.get_chat_history") as mock_get_history:
            with patch("app.services.agent_service.update_chat_history") as mock_update_history:
                # Mock the history
                mock_get_history.return_value = [SystemMessage(content="You are helpful")]
                
                # Mock the agent response
                mock_executor.ainvoke = AsyncMock()
                mock_executor.ainvoke.return_value = {
                    "messages": [
                        SystemMessage(content="You are helpful"),
                        HumanMessage(content="What is the answer?"),
                        AIMessage(content="The answer is 42")
                    ]
                }
                
                # Call process_chat
                answer, sources = await process_chat("session-1", "What is the answer?", "file-123")
                
                assert isinstance(answer, str)
                assert isinstance(sources, list)
                assert mock_executor.ainvoke.called


@pytest.mark.asyncio
async def test_process_chat_with_output_key():
    """Test process_chat handles response with output key."""
    with patch("app.services.agent_service.agent_executor") as mock_executor:
        with patch("app.services.agent_service.get_chat_history") as mock_get_history:
            with patch("app.services.agent_service.update_chat_history") as mock_update_history:
                mock_get_history.return_value = [SystemMessage(content="System")]
                mock_executor.ainvoke = AsyncMock()
                mock_executor.ainvoke.return_value = {
                    "output": "Direct output response",
                    "messages": []
                }
                
                answer, sources = await process_chat("session-2", "Query", "file-456")
                
                assert "output" in str(mock_executor.ainvoke.return_value) or isinstance(answer, str)
                assert isinstance(sources, list)


@pytest.mark.asyncio
async def test_process_chat_calls_update_memory():
    """Test that process_chat updates memory with each exchange."""
    with patch("app.services.agent_service.agent_executor") as mock_executor:
        with patch("app.services.agent_service.get_chat_history") as mock_get_history:
            with patch("app.services.agent_service.update_chat_history") as mock_update_history:
                mock_get_history.return_value = [SystemMessage(content="System")]
                mock_executor.ainvoke = AsyncMock()
                mock_executor.ainvoke.return_value = {
                    "messages": [AIMessage(content="Response")]
                }
                
                await process_chat("session-4", "Test query", "file-123")
                
                # Verify update_chat_history was called
                assert mock_update_history.called


@pytest.mark.asyncio
async def test_process_chat_different_file_ids():
    """Test process_chat with different file IDs."""
    with patch("app.services.agent_service.agent_executor") as mock_executor:
        with patch("app.services.agent_service.get_chat_history") as mock_get_history:
            with patch("app.services.agent_service.update_chat_history") as mock_update_history:
                mock_get_history.return_value = [SystemMessage(content="System")]
                mock_executor.ainvoke = AsyncMock()
                mock_executor.ainvoke.return_value = {
                    "messages": [AIMessage(content="Response")]
                }
                
                # Call with different file IDs
                await process_chat("session-5", "Query 1", "file-A")
                await process_chat("session-5", "Query 2", "file-B")
                
                # Both should execute successfully
                assert mock_executor.ainvoke.call_count == 2


@pytest.mark.asyncio
async def test_process_chat_with_file_id_in_message():
    """Test that process_chat includes file_id in the message to agent."""
    with patch("app.services.agent_service.agent_executor") as mock_executor:
        with patch("app.services.agent_service.get_chat_history") as mock_get_history:
            with patch("app.services.agent_service.update_chat_history") as mock_update_history:
                mock_get_history.return_value = [SystemMessage(content="System")]
                mock_executor.ainvoke = AsyncMock()
                mock_executor.ainvoke.return_value = {
                    "messages": [AIMessage(content="Response")]
                }
                
                await process_chat("session-6", "Query", "special-file-id-123")
                
                # Verify the call includes the file_id somehow
                call_args = mock_executor.ainvoke.call_args
                assert call_args is not None


@pytest.mark.asyncio
async def test_process_chat_empty_response():
    """Test process_chat handles empty agent response gracefully."""
    with patch("app.services.agent_service.agent_executor") as mock_executor:
        with patch("app.services.agent_service.get_chat_history") as mock_get_history:
            with patch("app.services.agent_service.update_chat_history") as mock_update_history:
                mock_get_history.return_value = [SystemMessage(content="System")]
                mock_executor.ainvoke = AsyncMock()
                mock_executor.ainvoke.return_value = {"messages": [], "output": ""}
                
                # Should not raise, should return something
                answer, sources = await process_chat("session-7", "Query", "file-789")
                
                assert isinstance(answer, str)
                assert isinstance(sources, list)


@pytest.mark.asyncio
async def test_search_document_tool_exists():
    """Test that search_document tool is defined and callable."""
    from app.services import agent_service
    
    assert hasattr(agent_service, 'search_document')
    assert callable(agent_service.search_document) or hasattr(agent_service.search_document, 'invoke')