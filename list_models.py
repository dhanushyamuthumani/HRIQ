import ollama
try:
    models = ollama.list()
    print("Models found:")
    for m in models.get('models', []):
        print(f"- {m.get('name')}")
except Exception as e:
    print(f"Error: {e}")
