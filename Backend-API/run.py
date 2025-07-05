"""
@Author: Borja Otero Ferreira
Entry point for IALab Suite API
"""
import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.app import create_app

def main():
    # Get environment configuration
    config_name = os.environ.get('FLASK_ENV', 'development')
    
    # Create application
    app, socketio = create_app(config_name)
    
    # Get host and port from environment or use defaults
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 8081))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    use_reloader = os.environ.get('USE_RELOADER', 'False').lower() == 'true'
    
    print(f"🚀 Starting IALab Suite API on {host}:{port}")
    print(f"🔧 Environment: {config_name}")
    print(f"🐛 Debug mode: {debug}")
    print(f"🔄 Auto-reload: {use_reloader}")
    
    # Run the application
    socketio.run(
        app,
        host=host,
        port=port,
        debug=debug,
        use_reloader=use_reloader,
        allow_unsafe_werkzeug=True
    )

if __name__ == '__main__':
    main()
