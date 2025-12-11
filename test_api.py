#!/usr/bin/env python3
"""
Quick API test to diagnose OpenAI issues
"""

import os
from openai import OpenAI

# Load API key from environment variable
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("[ERROR] OPENAI_API_KEY environment variable not set")
    print("[INFO] Add to .env file: OPENAI_API_KEY=sk-...")
    exit(1)

client = OpenAI(api_key=api_key)

print("[TEST] Checking OpenAI API Status...\n")

# Test 1: List available models
try:
    print("[TEST 1] Listing available models...\n")
    models = client.models.list()
    available_models = [m.id for m in models.data if 'gpt' in m.id]
    print(f"Available GPT models: {available_models}\n")
except Exception as e:
    print(f"[ERROR] Failed to list models: {str(e)}\n")

# Test 2: Simple API call with gpt-3.5-turbo
try:
    print("[TEST 2] Testing GPT-3.5-turbo API call...\n")
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Say 'API works'"}],
        max_tokens=10
    )
    print(f"[SUCCESS] GPT-3.5-turbo works: {response.choices[0].message.content}\n")
except Exception as e:
    print(f"[ERROR] GPT-3.5-turbo failed: {str(e)}\n")

# Test 3: Try gpt-4o
try:
    print("[TEST 3] Testing GPT-4o API call...\n")
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "Say 'API works'"}],
        max_tokens=10
    )
    print(f"[SUCCESS] GPT-4o works: {response.choices[0].message.content}\n")
except Exception as e:
    print(f"[ERROR] GPT-4o failed: {str(e)}\n")

print("[RECOMMENDATION]\n")
print("If GPT-3.5-turbo works but GPT-4o doesn't:")
print("  → Your account may not have access to GPT-4o")
print("  → Switch to GPT-3.5-turbo (still accurate for route parsing)\n")

print("If both fail:")
print("  → Check your API key is valid")
print("  → Check your account has credits")
print("  → Visit https://platform.openai.com/account/billing/overview\n")
