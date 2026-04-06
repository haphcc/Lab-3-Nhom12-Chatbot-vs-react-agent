# Setup Guide: Search Use Case (Mock Data)

This guide is for the **Information Search Agent** use case (Search/Wikipedia/Calculator/Fact-check) using deterministic **mock datasets**.

## 1) Environment Variables

Copy `.env.example` to `.env` and fill your keys if you want to use real providers.

- OpenAI: set `OPENAI_API_KEY`
- Gemini: set `GEMINI_API_KEY`
- Local: set `DEFAULT_PROVIDER=local` and `LOCAL_MODEL_PATH=./models/<your_model>.gguf`

## 2) Install Dependencies

```bash
pip install -r requirements.txt
```

## 3) Mock Data Location

The search tools read from:

- `src/tools/mock_data/search_results.json`
- `src/tools/mock_data/wikipedia_articles.json`

You can edit these JSON files to add more deterministic cases for demos.

## 4) Run Demos

### Interactive Search Demo

```bash
python search_demo.py --provider openai --model gpt-4o
```

### Chatbot vs Agent Comparison (Search)

```bash
python compare_search.py --prompt "Gia vang hom nay o Viet Nam la bao nhieu?"
```

### Multi-hop Search Demo

```bash
python multi_hop_demo.py
```

## 5) Troubleshooting

1. **Tool returns "Khong tim thay..."**
   - Add a matching key to `src/tools/mock_data/search_results.json`.

2. **Local provider fails**
   - Ensure `llama-cpp-python` installed and `LOCAL_MODEL_PATH` points to an existing `.gguf` file.

3. **Gemini warning about deprecated package**
   - It's a warning; the demo may still run. If it blocks, switch provider to OpenAI or Local for the demo.
