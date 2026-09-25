from llama_cpp import Llama

llm = Llama(
    model_path="C:/Aegentix/models/mistral-7b.Q4_K_M.gguf",
    n_ctx=4096,
    n_threads=4
)

print("Mistral-7B loaded! Type your question:")
print("Type 'exit' to quit\n")

while True:
    user = input("You: ").strip()
    if user.lower() == "exit":
        break
    
    response = llm.create_chat_completion(
        messages=[{"role": "user", "content": user}],
        max_tokens=300
    )
    
    print("AI:", response["choices"][0]["message"]["content"])
    print()
