"""
@Author: Borja Otero Ferreira
Chat service for IALab Suite API
"""
from typing import List, Dict, Any, Optional
from app.models.data_models import ChatHistory, ApiResponse
from app.utils.file_manager import file_manager
from app.utils.logger import logger

class ChatService:
    """Service for chat-related operations"""
    
    def save_chat(self, name: str, history: Dict[str, Any]) -> ApiResponse:
        """Save chat history"""
        try:
            success = file_manager.save_chat_history(name, history)
            
            if success:
                return ApiResponse(
                    success=True,
                    message=f"Chat '{name}' saved successfully"
                )
            else:
                return ApiResponse(
                    success=False,
                    message=f"Failed to save chat '{name}'",
                    error="File operation failed"
                )
                
        except Exception as e:
            logger.error(f"Error saving chat {name}: {e}")
            return ApiResponse(
                success=False,
                message=f"Error saving chat '{name}'",
                error=str(e)
            )
    
    def load_chat(self, name: str) -> ApiResponse:
        """Load chat history"""
        try:
            history = file_manager.load_chat_history(name)
            
            if history is not None:
                return ApiResponse(
                    success=True,
                    message=f"Chat '{name}' loaded successfully",
                    data=history
                )
            else:
                return ApiResponse(
                    success=False,
                    message=f"Chat '{name}' not found",
                    error="Chat not found"
                )
                
        except Exception as e:
            logger.error(f"Error loading chat {name}: {e}")
            return ApiResponse(
                success=False,
                message=f"Error loading chat '{name}'",
                error=str(e)
            )
    
    def delete_chat(self, name: str) -> ApiResponse:
        """Delete chat history"""
        try:
            success = file_manager.delete_chat_history(name)
            
            if success:
                return ApiResponse(
                    success=True,
                    message=f"Chat '{name}' deleted successfully"
                )
            else:
                return ApiResponse(
                    success=False,
                    message=f"Chat '{name}' not found",
                    error="Chat not found"
                )
                
        except Exception as e:
            logger.error(f"Error deleting chat {name}: {e}")
            return ApiResponse(
                success=False,
                message=f"Error deleting chat '{name}'",
                error=str(e)
            )
    
    def list_chats(self) -> ApiResponse:
        """List all available chats"""
        try:
            chats = file_manager.list_chat_histories()
            
            return ApiResponse(
                success=True,
                message=f"Found {len(chats)} chats",
                data=chats
            )
            
        except Exception as e:
            logger.error(f"Error listing chats: {e}")
            return ApiResponse(
                success=False,
                message="Error listing chats",
                error=str(e)
            )

# Global chat service instance
chat_service = ChatService()
