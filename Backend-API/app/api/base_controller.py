"""
@Author: Borja Otero Ferreira
Base controller for IALab Suite API
"""
from flask import jsonify, request
from typing import Dict, Any
from app.models.data_models import ApiResponse
from app.utils.logger import logger

class BaseController:
    """Base controller with common functionality"""
    
    def _create_response(self, response: ApiResponse, status_code: int = 200):
        """Create standardized JSON response"""
        return jsonify(response.to_dict()), status_code
    
    def _get_json_data(self) -> Dict[str, Any]:
        """Safely get JSON data from request"""
        try:
            return request.get_json() or {}
        except Exception as e:
            logger.error(f"Error parsing JSON data: {e}")
            return {}
    
    def _handle_error(self, error: Exception, message: str = "Internal server error") -> tuple:
        """Handle errors consistently"""
        logger.error(f"{message}: {error}")
        response = ApiResponse(
            success=False,
            message=message,
            error=str(error)
        )
        return self._create_response(response, 500)
