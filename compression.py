import base64


def compress_text(text, dictionary):
    for phrase, symbol in dictionary.items():
        text = text.replace(phrase, symbol)
    compressed_text = base64.b64encode(text.encode('utf-8')).decode('utf-8')
    return compressed_text


def decompress_text(compressed_text, dictionary):
    text = base64.b64decode(compressed_text).decode('utf-8')
    for symbol, phrase in dictionary.items():
        text = text.replace(symbol, phrase)
    return text
