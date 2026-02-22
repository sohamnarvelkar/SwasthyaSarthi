"""Simple test for observability"""
from agents.llm_provider import get_llm, is_tracing_enabled

# Test
tracing = is_tracing_enabled()
llm = get_llm()

# Write results to file
with open("test_output.txt", "w") as f:
    f.write(f"Tracing enabled: {tracing}\n")
    f.write(f"LLM available: {llm is not None}\n")
    if llm:
        f.write(f"LLM type: {type(llm).__name__}\n")

print("Check test_output.txt")
