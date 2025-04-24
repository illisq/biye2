#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
from dotenv import load_dotenv
from openai import OpenAI
import json

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Load environment variables
load_dotenv()

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE")
AI_MODEL = os.getenv("AI_MODEL", "gpt-4")

def test_openai_api():
    """Test OpenAI API connectivity using openai>=1.0.0"""
    if not OPENAI_API_KEY:
        print("OpenAI API key not found in .env file")
        return False

    try:
        # Create a client using the new OpenAI class
        client = OpenAI(
            api_key=OPENAI_API_KEY,
            base_url=OPENAI_API_BASE if OPENAI_API_BASE else None
        )

        print(f"Using OpenAI API Base URL: {OPENAI_API_BASE or 'default'}")
        print(f"Using AI Model: {AI_MODEL}")

        response = client.chat.completions.create(
            model=AI_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello, are you working?"}
            ]
        )

        print("OpenAI API Test: SUCCESS")
        print(f"Response: {response.choices[0].message.content}")
        return True

    except Exception as e:
        print(f"OpenAI API Test: FAILED - {str(e)}")
        return False


if __name__ == "__main__":
    print("Testing API connections...")
    print("=" * 50)

    print("\n[1/1] Testing OpenAI compatible API connection")
    openai_ok = test_openai_api()

    print("\n" + "=" * 50)
    print("Test Results Summary:")
    print(f"OpenAI API: {'[Working]' if openai_ok else '[Failed]'}")
