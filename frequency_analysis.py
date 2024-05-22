
from collections import Counter
from nltk import ngrams
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer

def get_frequent_words(text, top_n=10):
    words = word_tokenize(text)
    word_counts = Counter(words)
    return word_counts.most_common(top_n)

def get_frequent_ngrams(text, n=2, top_n=10):
    words = word_tokenize(text)
    n_grams = ngrams(words, n)
    n_gram_counts = Counter(n_grams)
    return n_gram_counts.most_common(top_n)

def get_tfidf_scores(documents):
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(documents)
    feature_names = vectorizer.get_feature_names_out()
    tfidf_scores = []
    for doc_idx, doc in enumerate(tfidf_matrix):
        scores = {feature_names[word_idx]: score for word_idx, score in zip(doc.indices, doc.data)}
        tfidf_scores.append(scores)
    return tfidf_scores
