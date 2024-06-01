import base64
from frequency_analysis import get_frequent_words, get_frequent_ngrams

def build_compression_dictionary(texts, top_n=100):
    all_text = ' '.join(texts)
    frequent_words = get_frequent_words(all_text, top_n)
    frequent_phrases = get_frequent_ngrams(all_text, 2, top_n)

    dictionary = {}
    for i, (word, _) in enumerate(frequent_words):
        dictionary[word] = f"__W{i}__"
    for i, ((word1, word2), _) in enumerate(frequent_phrases):
        phrase = f"{word1} {word2}"
        dictionary[phrase] = f"__P{i}__"

    return dictionary


def compress_text(text, dictionary):
    for phrase, symbol in dictionary.items():
        text = text.replace(phrase, symbol)
    compressed_text = base64.b64encode(text.encode('utf-8')).decode('utf-8')
    return compressed_text


def decompress_text(compressed_text, dictionary):
    text = base64.b64decode(compressed_text).decode('utf-8')
    reverse_dictionary = {v: k for k, v in dictionary.items()}
    for symbol, phrase in reverse_dictionary.items():
        text = text.replace(symbol, phrase)
    return text
