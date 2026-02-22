"""
Test LangSmith Observability Integration
"""
import os

results = []

results.append("=" * 60)
results.append("Testing LangSmith Observability Integration")
results.append("=" * 60)

# Check environment variables
results.append("\n1. Environment Configuration:")
results.append(f"   LANGSMITH_API_KEY: {'Set' if os.getenv('LANGSMITH_API_KEY') else 'Not Set'}")
results.append(f"   LANGSMITH_PROJECT: {os.getenv('LANGSMITH_PROJECT', 'Not Set')}")
results.append(f"   LANGCHAIN_TRACING_V2: {os.getenv('LANGCHAIN_TRACING_V2', 'Not Set')}")

# Test LLM Provider
results.append("\n2. Testing LLM Provider:")
from agents.llm_provider import get_llm, is_tracing_enabled, invoke_with_trace
results.append(f"   Tracing Enabled: {is_tracing_enabled()}")

llm = get_llm()
if llm:
    results.append(f"   LLM Available: Yes")
    results.append(f"   LLM Type: {type(llm).__name__}")
else:
    results.append(f"   LLM Available: No (will use rule-based)")

# Test invoke_with_trace function
results.append("\n3. Testing invoke_with_trace:")
result = invoke_with_trace("Say 'Hello from LangSmith!' in exactly 5 words.", agent_name="test")
results.append(f"   Result: {result}")

# Test graph compilation
results.append("\n4. Testing Graph Compilation:")
from orchestration.graph import app_graph
results.append(f"   Graph Compiled: Yes")
results.append(f"   Graph Nodes: {list(app_graph.nodes.keys())}")

# Summary
results.append("\n" + "=" * 60)
results.append("Observability Setup Complete!")
results.append("=" * 60)
results.append("\nTo view traces in LangSmith:")
results.append("1. Set LANGSMITH_API_KEY in .env file")
results.append("2. Go to https://smith.langchain.com/")
results.append("3. Select project 'swasthya-sarthi'")
results.append("=" * 60)

# Write to file
with open("observability_test.txt", "w") as f:
    f.write("\n".join(results))

print("Done - see observability_test.txt")
