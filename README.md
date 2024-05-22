
# Token Reduction Package

This package provides tools for compressing and decompressing text, analyzing word and phrase frequencies, and sending requests to the GPT API.

## Modules

- `compression`: Functions for compressing and decompressing text using a dictionary and base64 encoding.
- `frequency_analysis`: Functions for analyzing word and n-gram frequencies, as well as calculating TF-IDF scores.
- `api_client`: Function to send requests to the GPT API.

## Usage

### Compression and Decompression

```python
from token_reduction import compress_text, decompress_text

dictionary = {"Unity": "A", "virtual sandbox machine": "B", "full autonomy": "C"}
text = "Unity is a virtual sandbox machine with full autonomy."
compressed_text = compress_text(text, dictionary)
decompressed_text = decompress_text(compressed_text, dictionary)
```

### Frequency Analysis

```python
from token_reduction import get_frequent_words, get_frequent_ngrams, get_tfidf_scores

text = "This is a sample text. This text is for testing text analysis."
frequent_words = get_frequent_words(text)
frequent_ngrams = get_frequent_ngrams(text, n=2)
documents = ["This is a sample text.", "This text is for testing text analysis."]
tfidf_scores = get_tfidf_scores(documents)
```

### Sending GPT API Request

```python
from token_reduction import send_gpt_request

api_key = "your_api_key"
model = "gpt-4o-2024-05-13"
prompt = "Hello, how are you?"
response = send_gpt_request(api_key, model, prompt)
print(response)
```
