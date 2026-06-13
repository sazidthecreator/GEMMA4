from langchain_ollama import OllamaLLM

llm = OllamaLLM(model="gemma4")
response = llm.invoke("Explain the concept of zero-cost architecture in short.")
print(response)