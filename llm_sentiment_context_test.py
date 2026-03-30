#!/usr/bin/env python3
"""
LLM Context Test - User Prompts Edition
Real user-style LLM questions + lib analysis context vs plain
"""

import requests
import json
import time
import csv
import os
from datetime import datetime
from textblob import TextBlob
import yake

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2:1b"

def query_ollama(prompt):
    data = {"model": MODEL, "prompt": prompt, "stream": False, "options": {"temperature": 0.7}}
    resp = requests.post(OLLAMA_URL, json=data, timeout=45)
    return resp.json().get("response", "") if resp.ok else None

def analyze_libs(text):
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    sentiment = "POSITIVE" if polarity > 0.1 else "NEGATIVE" if polarity < -0.1 else "NEUTRAL"
    
    kw_extractor = yake.KeywordExtractor(lan="en", n=3, dedupLim=0.9, top=8)
    keywords = [kw[0] for kw in kw_extractor.extract_keywords(text)[:8]]
    
    return sentiment, keywords

def test_user_prompts(text):
    user_questions = [
        "What is the main idea? How should I respond?",
        "What action should I take? Summarize key points.",
        "How would you reply to this email?",
        "What are the risks here? What is the sentiment?",
        "Give me 3 bullet points and suggested reply.",
        "Is this good or bad news? Next steps?"
    ]
    
    sentiment, keywords = analyze_libs(text)
    print(f"\n📄 TEXT: {text[:120]}...")
    print(f"🔍 LIBS: {sentiment} | {keywords[:5]}")
    
    for q in user_questions:
        # PLAIN
        plain_prompt = f"User: {q}\n\nText: {text}\n\nLLM:"
        plain_start = time.time()
        plain_resp = query_ollama(plain_prompt)
        plain_time = (time.time() - plain_start)*1000
        
        # CONTEXT
        context_prompt = f"""LIBS: Sentiment={sentiment}, Keywords={', '.join(keywords)}

User: {q}

Text: {text}

Answer using analysis:"""
        context_start = time.time()
        context_resp = query_ollama(context_prompt)
        context_time = (time.time() - context_start)*1000
        
        print(f"\n❓ {q[:60]}...")
        print(f"  Plain ({plain_time:.0f}ms): {plain_resp[:150] if plain_resp else 'FAIL'}")
        print(f"  Context ({context_time:.0f}ms): {context_resp[:150] if context_resp else 'FAIL'}")
        
        save_result(text[:80], q[:50], sentiment, str(keywords[:4]), plain_resp[:100], context_resp[:100], plain_time, context_time)

def save_result(text, question, sentiment, keywords, plain_r, context_r, p_time, c_time):
    filename = "user_prompts_results.csv"
    mode = 'w' if not os.path.exists(filename) else 'a'
    
    with open(filename, mode, newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if mode == 'w':
            writer.writerow(['timestamp', 'text_sample', 'question', 'sentiment', 'keywords', 'plain_resp', 'context_resp', 'plain_ms', 'context_ms'])
        writer.writerow([datetime.now().isoformat(), text, question, sentiment, keywords, plain_r, context_r, round(p_time), round(c_time)])

def user_texts():
    return [
        "Our Q4 exceeded expectations! 28% revenue growth. Team outstanding!",
        "Customer service failed. 340% complaints up. Urgent action needed.",
        "CPU 87% peak. Memory 64GB. No alerts. Stable throughput.",
        "Frontend excellent 120fps. Backend OK. Docs missing.",
        "Formal warning for attendance policy violations. Termination next."
    ]

def main():
    print("👤 USER PROMPTS TEST - Real LLM questions")
    print("ollama serve required")
    
    if os.path.exists("user_prompts_results.csv"):
        os.remove("user_prompts_results.csv")
    
    for text in user_texts():
        test_user_prompts(text)
    
    print("\n✅ SAVED user_prompts_results.csv")
    print("Compare plain vs context-aware responses!")

if __name__ == "__main__":
    main()

