from llama_cpp import Llama

print('')
print('🔍 LOADING MISTRAL-7B...')
print('-' * 40)

try:
    llm = Llama(
        model_path='C:/Aegentix/models/mistral-7b.Q4_K_M.gguf',
        n_ctx=4096,
        n_threads=4,
        verbose=False,
        use_mmap=True
    )
    print('   ✅ Mistral-7B loaded successfully')
    print('   📊 Context: 4096')
    print('   🧠 Model: Mistral-7B-Instruct-v0.2')
    print('')
    print('💬 You are now in conversation with Mistral-7B.')
    print('   Type your questions naturally.')
    print('   Type "exit" to quit.')
    print('')

    while True:
        user_input = input('🧠 You: ').strip()

        if not user_input:
            continue

        if user_input.lower() in ['exit', 'quit', 'goodbye']:
            print('   👋 Goodbye.')
            break

        print('   💭 Thinking...')

        response = llm.create_chat_completion(
            messages=[
                {'role': 'system', 'content': 'You are a helpful AI assistant. Be concise and accurate. Do not make up information.'},
                {'role': 'user', 'content': user_input}
            ],
            max_tokens=300,
            temperature=0.7
        )

        result = response['choices'][0]['message']['content'].strip()
        print(f'   🤖 {result}')
        print('')

except Exception as e:
    print(f'   ❌ Error: {e}')
