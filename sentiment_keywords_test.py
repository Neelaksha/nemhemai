#!/usr/bin/env python3
"""
Sentiment Analysis & Keyword Extraction Test File - with CSV export & timing
Tests TextBlob + YAKE without changing Nemhem project
Run: pip install textblob yake && python sentiment_keywords_test.py
Generates results.csv with timing data
"""

import sys
import time
import csv
import os
from datetime import datetime
from textblob import TextBlob
import yake

def save_result(method, task, text_sample, score1, score2, label, exec_time):
    """Save result to CSV"""
    filename = "results_lib.csv"
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

def test_sentiment(text):
    """Test sentiment analysis with TextBlob"""
    start_time = time.time()
    
    print("\n" + "="*60)
    print("SENTIMENT ANALYSIS (TextBlob)")
    print("="*60)
    print(f"Text: {text}")
    
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    subjectivity = blob.sentiment.subjectivity
    
    # Convert polarity to label
    if polarity > 0.1:
        sentiment_label = "POSITIVE"
    elif polarity < -0.1:
        sentiment_label = "NEGATIVE"
    else:
        sentiment_label = "NEUTRAL"
    
    exec_time = (time.time() - start_time) * 1000  # ms
    print(f"Polarity: {polarity:.3f} ({sentiment_label})")
    print(f"Subjectivity: {subjectivity:.3f}")
    print(f"Time: {exec_time:.1f}ms")
    
    save_result("TextBlob", "sentiment", text[:100], polarity, subjectivity, sentiment_label, exec_time)
    print("Saved to results_lib.csv")

def test_keywords(text, num_keywords=10):
    """Test keyword extraction with YAKE"""
    start_time = time.time()
    
    print("\n" + "="*60)
    print("KEYWORD EXTRACTION (YAKE)")
    print("="*60)
    print(f"Text: {text[:100]}...")
    
    kw_extractor = yake.KeywordExtractor(
        lan="en", n=3, dedupLim=0.9, top=num_keywords, features=None
    )
    
    keywords = kw_extractor.extract_keywords(text)
    
    keyword_str = "; ".join([kw[0] for kw in keywords[:num_keywords]])
    exec_time = (time.time() - start_time) * 1000
    
    print("Top Keywords:")
    print("-" * 30)
    for i, (keyword, score) in enumerate(keywords[:num_keywords], 1):
        print(f"{i:2d}. {keyword:25s} (score: {score:.3f})")
    print(f"Time: {exec_time:.1f}ms")
    
    save_result("YAKE", "keywords", text[:100], len(keywords), keyword_str[:50], "top_keywords", exec_time)
    print("Saved to results_lib.csv")

def demo_texts():
    """Test samples"""
    return [
        "I'm absolutely thrilled about the new project! This is going to be amazing.",
        "The service was terrible. Never coming back. Waste of money.",
        "The weather is okay today. Not too bad.",
        "Python is a versatile language used in AI, web development, and data science. Django and Flask are popular web frameworks.",
        "Climate change is the biggest threat facing humanity in the 21st century."
    ]

def interactive_test():
    """Interactive mode"""
    print("\nInteractive Test Mode (Ctrl+C to exit)")
    print("-" * 40)
    
    while True:
        try:
            text = input("\nEnter text (or 'demo' for samples, 'quit'): ").strip()
            if text.lower() == 'quit':
                break
            elif text.lower() == 'demo':
                for sample in demo_texts():
                    test_sentiment(sample)
                    test_keywords(sample, 8)
                continue
            elif not text:
                print("Please enter text!")
                continue
            
            test_sentiment(text)
            test_keywords(text, 8)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")

def main():
    """Main"""
    # Clear old CSV
    if os.path.exists("results_lib.csv"):
        os.remove("results_lib.csv")
    
    print("Lib Tests (TextBlob + YAKE) - Results → results_lib.csv")
    print("-" * 50)
    
    for sample in demo_texts():
        test_sentiment(sample)
        test_keywords(sample, 8)
    
    print("\nDemo complete! Check results_lib.csv")
    interactive_test()

if __name__ == "__main__":
    main()

