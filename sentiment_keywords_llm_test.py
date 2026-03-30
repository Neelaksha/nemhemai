#!/usr/bin/env python3
"""
Sentiment Analysis & Keyword Extraction Test - LLM Version
Uses Ollama (same as Nemhem backend) for comparison
Run: ollama pull llama3.2:1b && python sentiment_keywords_llm_test.py
"""

import requests
import json
import sys

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2:1b"  # Or "llama3.2:3b" if available

def query_ollama(prompt, model=MODEL, stream=False):
    """Query Ollama API (same as Nemhem backend)"""
    data = {
        "model": model,
        "prompt": prompt,
        "stream": stream,
        "options": {"temperature": 0.1, "top_p": 0.9}  # Low creativity for analysis
    }
    
    try:
        resp = requests.post(OLLAMA_URL, json=data, timeout=30)
        resp.raise_for_status()
        return resp.json().get("response", "")
    except Exception as e:
        print(f"Ollama error: {e}")
        return None

def test_sentiment_llm(text):
    """Test sentiment with LLM"""
    print("\n" + "="*70)
    print("SENTIMENT ANALYSIS (LLM/Ollama)")
    print("="*70)
    print(f"Text: {text}\n")
    
    prompt = f"""Analyze the sentiment of this text. Respond ONLY with valid JSON:

{{
  "sentiment": "positive|negative|neutral|mixed",
  "confidence": 0-100,
  "emotions": ["joy", "anger", "sadness", ...] (0-3 max),
  "tone": "formal|casual|professional|enthusiastic|sarcastic|..."
}}

Text: {text}"""
    
    result = query_ollama(prompt)
    if result:
        try:
            parsed = json.loads(result.strip('```json\n').strip('```'))
            print(json.dumps(parsed, indent=2))
        except:
            print("Raw LLM response:", result[:200] + "..." if len(result)>200 else result)
    else:
        print("No response (check if Ollama running: ollama serve)")

def test_keywords_llm(text, top_n=10):
    """Test keywords with LLM"""
    print("\n" + "="*70)
    print("KEYWORD EXTRACTION (LLM/Ollama)")
    print("="*70)
    print(f"Text: {text[:100]}...\n")
    
    prompt = f"""Extract the top {top_n} most important keywords/phrases from this text.
Return ONLY valid JSON array of keywords ranked by importance.

{{
  "keywords": [
    "keyword1",
    "keyword2", 
    "important phrase"
  ],
  "total_found": 10
}}

Text: {text}"""
    
    result = query_ollama(prompt)
    if result:
        try:
            parsed = json.loads(result.strip('```json\n').strip('```'))
            print(json.dumps(parsed, indent=2))
        except:
            print("Raw LLM response:", result[:300] + "...")
    else:
        print("No response")

def demo_texts():
    """Same samples as non-LLM test"""
    return [
        "I'm absolutely thrilled about the new project! This is going to be amazing.",
        "The service was terrible. Never coming back. Waste of money.",
        "The weather is okay today. Not too bad.",
        "Python is a versatile language used in AI, web development, and data science. Django and Flask are popular web frameworks.",
        "Climate change is the biggest threat facing humanity in the 21st century."
    ]

def interactive_llm():
    """Interactive LLM test"""
    print("\nInteractive LLM Mode (Ctrl+C to exit)")
    print("-" * 50)
    
    while True:
        try:
            text = input("\nEnter text (or 'demo', 'quit'): ").strip()
            if text.lower() in ['quit', 'q']:
                break
            elif text.lower() == 'demo':
                for sample in demo_texts():
                    test_sentiment_llm(sample)
                    test_keywords_llm(sample)
                continue
            elif not text:
                continue
            
            test_sentiment_llm(text)
            test_keywords_llm(text, top_n=8)
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break

def main():
    """Main LLM test"""
    print("Sentiment & Keywords LLM Test (Ollama)")
    print("Start Ollama: ollama serve")
    print("Pull model: ollama pull llama3.2:1b")
    print("-" * 60)
    
    # Demo
    print("Testing LLM version...")
    for sample in demo_texts():
        test_sentiment_llm(sample)
        test_keywords_llm(sample)
    
    interactive_llm()

if __name__ == "__main__":
    main()

