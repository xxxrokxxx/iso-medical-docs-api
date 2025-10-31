"""
Test script for ISO Documents API
"""

import requests
import json

API_URL = "http://localhost:8080"

print("="*80)
print("Testing ISO Documents API")
print("="*80)

# Test 1: Health check
print("\n1. Health Check")
print("-" * 40)
response = requests.get(f"{API_URL}/health")
print(f"Status: {response.status_code}")
print(json.dumps(response.json(), indent=2))

# Test 2: Root endpoint
print("\n2. Root Endpoint")
print("-" * 40)
response = requests.get(f"{API_URL}/")
print(f"Status: {response.status_code}")
print(json.dumps(response.json(), indent=2))

# Test 3: Search
print("\n3. Semantic Search - 'risk management'")
print("-" * 40)
response = requests.post(
    f"{API_URL}/search",
    json={"query": "risk management", "limit": 2}
)
print(f"Status: {response.status_code}")
results = response.json()
for i, result in enumerate(results, 1):
    print(f"\nResult {i}:")
    print(f"  Title: {result['title']}")
    print(f"  Distance: {result['distance']:.4f}")
    print(f"  Text: {result['text'][:150]}...")

# Test 4: RAG Question
print("\n4. RAG Question Answering")
print("-" * 40)
question = "What is ISO 14971?"
print(f"Question: {question}")
response = requests.post(
    f"{API_URL}/ask",
    json={"question": question, "limit": 3}
)
print(f"Status: {response.status_code}")
data = response.json()
print(f"\nAnswer:")
print(data['answer'])
print(f"\n{len(data['sources'])} sources used")

print("\n" + "="*80)
print("✓ All tests completed!")
print("="*80)
