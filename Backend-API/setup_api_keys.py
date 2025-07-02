#!/usr/bin/env python
"""
Setup script para configurar las API keys de IALab Suite
"""
import os
import shutil

def main():
    print("🔧 IALab Suite API Keys Setup")
    print("=" * 40)
    
    # Verificar si existe .env
    if os.path.exists('.env'):
        print("✅ .env file already exists")
        
        response = input("Do you want to reconfigure API keys? (y/N): ")
        if response.lower() != 'y':
            print("Setup cancelled.")
            return
    else:
        print("📝 Creating .env file from template...")
        if os.path.exists('.env.example'):
            shutil.copy('.env.example', '.env')
            print("✅ .env file created from .env.example")
        else:
            print("❌ .env.example not found!")
            return
    
    print("\n🔑 Configure your API keys:")
    print("(Press Enter to skip any key)")
    
    # Leer archivo .env actual
    env_content = {}
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                line = line.strip()
                if line and '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    env_content[key] = value
    
    # Configurar API keys
    api_keys = {
        'YOUTUBE_API_KEY': 'YouTube Data API v3 key',
        'SERPER_API_KEY': 'Serper.dev API key for Google Search',
        'OPENAI_API_KEY': 'OpenAI API key',
        'ANTHROPIC_API_KEY': 'Anthropic Claude API key'
    }
    
    for key, description in api_keys.items():
        current = env_content.get(key, '')
        current_display = f"(current: {'*' * 10}...{current[-10:]})" if len(current) > 10 else f"(current: {current})" if current else "(not set)"
        
        print(f"\n{key} - {description}")
        print(f"Current value: {current_display}")
        new_value = input(f"Enter new value (or press Enter to keep current): ").strip()
        
        if new_value:
            env_content[key] = new_value
            print("✅ Updated")
        else:
            print("⏭️  Keeping current value")
    
    # Escribir archivo .env actualizado
    with open('.env', 'w') as f:
        f.write("# IALab Suite API Environment Configuration\n\n")
        f.write("# Flask Configuration\n")
        f.write(f"FLASK_ENV={env_content.get('FLASK_ENV', 'development')}\n")
        f.write(f"SECRET_KEY={env_content.get('SECRET_KEY', 'dev-secret-key-change-in-production')}\n")
        f.write(f"HOST={env_content.get('HOST', '0.0.0.0')}\n")
        f.write(f"PORT={env_content.get('PORT', '8081')}\n\n")
        
        f.write("# Model Configuration\n")
        f.write(f"MODELS_DIRECTORY={env_content.get('MODELS_DIRECTORY', 'Z:/Modelos LM Studio/')}\n")
        f.write(f"DEFAULT_MODEL_PATH={env_content.get('DEFAULT_MODEL_PATH', 'Z:/Modelos LM Studio/lmstudio-community/gemma-3-12b-it-GGUF/gemma-3-12b-it-Q4_K_M.gguf')}\n\n")
        
        f.write("# Cortex Tool API Keys\n")
        for key in api_keys.keys():
            f.write(f"{key}={env_content.get(key, '')}\n")
        f.write("\n")
        
        f.write("# Logging Configuration\n")
        f.write(f"LOG_LEVEL={env_content.get('LOG_LEVEL', 'INFO')}\n")
    
    print("\n✅ Configuration saved to .env")
    print("\n📋 API Key Resources:")
    print("• YouTube API: https://console.cloud.google.com/")
    print("• Serper API: https://serper.dev/")
    print("• OpenAI API: https://platform.openai.com/")
    print("• Anthropic API: https://console.anthropic.com/")
    print("\n🔒 Security: Never commit .env files to version control!")
    print("✅ Setup complete!")

if __name__ == "__main__":
    main()
