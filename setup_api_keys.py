#!/usr/bin/env python3
"""
Setup script for configuring API keys for enhanced VC analysis.
"""

import os
import sys
from pathlib import Path

def setup_api_keys():
    """Guide user through setting up API keys"""
    print("🔧 Setting up API Keys for Enhanced VC Analysis")
    print("=" * 50)
    
    # Check if .env file exists
    env_file = Path(".env")
    env_content = ""
    
    if env_file.exists():
        with open(env_file, 'r') as f:
            env_content = f.read()
        print("📄 Found existing .env file")
    else:
        print("📄 Creating new .env file")
    
    # OpenAI API Key
    print("\n🔑 OpenAI API Key Setup")
    print("-" * 30)
    print("You need an OpenAI API key to use GPT-4 for enhanced analysis.")
    print("Get your API key from: https://platform.openai.com/api-keys")
    
    current_openai_key = os.getenv("OPENAI_API_KEY")
    if current_openai_key and current_openai_key != "your_openai_api_key_here":
        print(f"✅ OpenAI API key already configured")
        openai_key = current_openai_key
    else:
        openai_key = input("Enter your OpenAI API key (or press Enter to skip): ").strip()
        if openai_key:
            print("✅ OpenAI API key will be configured")
        else:
            print("⚠️ OpenAI API key not provided - enhanced analysis will be limited")
    
    # SERPAPI Key (for web search)
    print("\n🔍 SERPAPI Key Setup (Optional)")
    print("-" * 30)
    print("SERPAPI enables web search for additional research.")
    print("Get your API key from: https://serpapi.com/")
    
    current_serpapi_key = os.getenv("SERPAPI_KEY")
    if current_serpapi_key and current_serpapi_key != "your_serpapi_key_here":
        print(f"✅ SERPAPI key already configured")
        serpapi_key = current_serpapi_key
    else:
        serpapi_key = input("Enter your SERPAPI key (or press Enter to skip): ").strip()
        if serpapi_key:
            print("✅ SERPAPI key will be configured")
        else:
            print("⚠️ SERPAPI key not provided - web search will be limited")
    
    # Update .env file
    new_env_content = ""
    
    # Add OpenAI key
    if openai_key:
        if "OPENAI_API_KEY=" in env_content:
            # Update existing
            lines = env_content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith("OPENAI_API_KEY="):
                    lines[i] = f"OPENAI_API_KEY={openai_key}"
                    break
            new_env_content = '\n'.join(lines)
        else:
            # Add new
            new_env_content = env_content + f"\nOPENAI_API_KEY={openai_key}"
    else:
        new_env_content = env_content
    
    # Add SERPAPI key
    if serpapi_key:
        if "SERPAPI_KEY=" in new_env_content:
            # Update existing
            lines = new_env_content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith("SERPAPI_KEY="):
                    lines[i] = f"SERPAPI_KEY={serpapi_key}"
                    break
            new_env_content = '\n'.join(lines)
        else:
            # Add new
            new_env_content = new_env_content + f"\nSERPAPI_KEY={serpapi_key}"
    
    # Write .env file
    with open(env_file, 'w') as f:
        f.write(new_env_content)
    
    print(f"\n✅ Configuration saved to {env_file}")
    
    # Test configuration
    print("\n🧪 Testing Configuration")
    print("-" * 30)
    
    # Reload environment
    from dotenv import load_dotenv
    load_dotenv()
    
    # Test OpenAI
    if os.getenv("OPENAI_API_KEY"):
        print("✅ OpenAI API key configured")
    else:
        print("❌ OpenAI API key not configured")
    
    # Test SERPAPI
    if os.getenv("SERPAPI_KEY"):
        print("✅ SERPAPI key configured")
    else:
        print("❌ SERPAPI key not configured")
    
    print("\n🎉 Setup Complete!")
    print("\nNext steps:")
    print("1. Restart the frontend to load the new configuration")
    print("2. Upload a pitch deck to test enhanced analysis")
    print("3. The system will now use GPT-4 for intelligent content extraction")
    
    return True

if __name__ == "__main__":
    setup_api_keys() 