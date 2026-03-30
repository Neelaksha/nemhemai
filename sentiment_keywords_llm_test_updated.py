#!/usr/bin/env python3
"""
Sentiment Analysis & Keyword Extraction LLM Test - with CSV export & timing
Same as Nemhem backend Ollama integration
Generates results_llm.csv
Run: ollama serve & ollama pull llama3.2:1b && python sentiment_keywords_llm_test_updated.py
"""

import requests
import json
import time
import csv
import os
import sys
from datetime import datetime

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2:1b"

def save_result(method, task, text_sample, score1, score2, label, exec_time):
    """Save to CSV"""
    filename = "results_llm.csv"
    file_exists = os.path.exists(filename)
    
    with open(filename, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['timestamp', 'method', 'task', 'text_sample', 'score1', 'score2', 'label', 'exec_time_ms'])
        
        writer.writerow([
            datetime.now().isoformat(),
            method,
            task,
            text_sample,
            score1,
            score2,
            label,
            round(exec_time, 1)
        ])

def query_ollama(prompt, model=MODEL):
    """Query Ollama (exact Nemhem backend function)"""
    data = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.1, "top_p": 0.9}
    }
    
    try:
        resp = requests.post(OLLAMA_URL, json=data, timeout=30)
        resp.raise_for_status()
        return resp.json().get("response", "")
    except Exception as e:
        print(f"Ollama error: {e}")
        return None

def test_sentiment_llm(text):
    """LLM sentiment with timing"""
    start_time = time.time()
    
    print("\n" + "="*70)
    print("LLM SENTIMENT (Ollama)")
    print("="*70)
    print(f"Text: {text}")
    
    prompt = f"""Analyze sentiment. JSON only:

{{
  "sentiment": "positive|negative|neutral",
  "confidence": 0-100,
  "emotions": ["joy","anger",...], 
  "tone": "formal|casual|..."
}}

Text: {text}"""
    
    result = query_ollama(prompt)
    exec_time = (time.time() - start_time) * 1000
    
    if result:
        try:
            parsed = json.loads(result.strip('```json\n').strip('```').strip())
            sentiment = parsed.get('sentiment', 'unknown')
            confidence = parsed.get('confidence', 0)
            emotions = str(parsed.get('emotions', []))
            print(json.dumps(parsed, indent=2))
            print(f"Time: {exec_time:.1f}ms")
            save_result("LLM", "sentiment", text[:100], confidence, sentiment, emotions[:50], exec_time)
        except:
            print("Parse error:", result[:200]+"...")
            save_result("LLM", "sentiment", text[:100], 0, "parse_error", result[:50], exec_time)
    else:
        print("No Ollama response")
        save_result("LLM", "sentiment", text[:100], 0, "no_response", "", exec_time)
    print("Saved to results_llm.csv")

def test_keywords_llm(text, top_n=10):
    """LLM keywords with timing"""
    start_time = time.time()
    
    print("\n" + "="*70)
    print("LLM KEYWORDS (Ollama)")
    print("="*70)
    print(f"Text: {text[:100]}...")
    
    prompt = f"""Extract top {top_n} keywords. JSON only:

{{
  "keywords": ["kw1","kw2","phrase"],
  "total": {top_n}
}}

Text: {text}"""
    
    result = query_ollama(prompt)
    exec_time = (time.time() - start_time) * 1000
    
    if result:
        try:
            parsed = json.loads(result.strip('```json\n').strip('```').strip())
            keywords = "; ".join(parsed.get('keywords', [])[:top_n])
            print(json.dumps(parsed, indent=2))
            print(f"Time: {exec_time:.1f}ms")
            save_result("LLM", "keywords", text[:100], parsed.get('total', 0), keywords[:50], "keywords", exec_time)
        except:
            print("Parse error:", result[:200]+"...")
            save_result("LLM", "keywords", text[:100], 0, "parse_error", result[:50], exec_time)
    else:
        print("No response")
        save_result("LLM", "keywords", text[:100], 0, "no_response", "", exec_time)
    print("Saved to results_llm.csv")

def demo_texts():
    return [
        "I'm absolutely thrilled about the new project! This is going to be amazing.",
        "The service was terrible. Never coming back. Waste of money.",
        "The weather is okay today. Not too bad.",
        "Python is a versatile language used in AI, web development, and data science.",
        "Climate change is the biggest threat facing humanity."
    ]

def interactive():
    print("\nInteractive (Ctrl+C exit)")
    print("-" * 40)
    
    while True:
        try:
            text = input("\nText (demo/quit): ").strip()
            if text.lower() == 'quit':
                break
            elif text.lower() == 'demo':
                for sample in demo_texts():
                    test_sentiment_llm(sample)
                    test_keywords_llm(sample)
            else:
                test_sentiment_llm(text)
                test_keywords_llm(text)
        except KeyboardInterrupt:
            break

def main():
    if os.path.exists("results_llm.csv"):
        os.remove("results_llm.csv")
    
    print("LLM Tests → results_llm.csv (ollama serve required)")
    print("-" * 60)
    
    for sample in demo_texts():
        test_sentiment_llm(sample)
        test_keywords_llm(sample)
    
    print("\nDemo done! results_lib.csv + results_llm.csv ready for comparison")
    interactive()

if __name__ == "__main__":
    main()

