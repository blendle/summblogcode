import numpy as np
import string
import nltk
from sklearn.feature_extraction.text import TfidfVectorizer

def tfidf_repr(sentences, stopwords, ngram_range):
    """
    Args:
        stemmed: List of sentences, every sentence as a string.
        stopwords: List of stopwords.

    Returns: TF*IDF representation of every sentence (np-array (#sentences * #tfs))

    """
    tfidf = TfidfVectorizer(stop_words=stopwords, ngram_range=ngram_range)
    tfidf_matrix = tfidf.fit_transform(sentences).toarray()

    idf_weight_dict = dict(zip(tfidf.get_feature_names(), tfidf.idf_))

    # Produce of dummy original indices (as in this case, all sentences are represented)
    original_indices = list(range(len(sentences)))

    return original_indices, tfidf_matrix, idf_weight_dict


def bigram_repr(stemmed, stopwords, svd, bigram_list):
    multi_hot_bigram_vectors = []
    for sentence in stemmed:
        # Exclude stopwords and punctuation and use stemmed words
        split_sentence = [stem for word, stem in sentence]
        # Turn sentence into list of bigrams
        bigrams = list(nltk.bigrams(split_sentence))
        # Make TF vector of bigram list, based on all bigrams in the data set
        multi_hot = np.array([v if k in bigrams else 0 for k, v in bigram_list])
        multi_hot_bigram_vectors.append(multi_hot)

    # Filter out non-hot vectors, and save original indices
    repr_list_with_orig_indices = [(i, s) for i, s in enumerate(multi_hot_bigram_vectors) if
                                   np.sum(s) != 0]

    original_indices, sentence_representations = zip(*repr_list_with_orig_indices)

    sentence_array = np.array(sentence_representations)
    sentence_repr = svd.transform(sentence_array)

    return original_indices, sentence_repr


def w2v_sentence_sums(tokenized, model, postagged, tagfilter):
    # define minimum number of words in the sentence that are also in the word model.
    min_word_vectors = 1

    # lowercase & split tokenized sentences
    preprocessed = [sentence.lower().split(' ')
                    for sentence in tokenized]

    # POS-tag filtering, and punctuation removal
    preprocessed = [[word.translate(str.maketrans('', '', string.punctuation))
                     for word_index, word in enumerate(sentence)]
                    for sentence_index, sentence in enumerate(preprocessed)]

    vectorized = [[model.model[word] for word in sentence
                   if word in model.model.vocab]
                  for sentence in preprocessed]

    sentence_sums_with_indices = [(index, np.sum(s, axis=0))
                                  for index, s in enumerate(vectorized)
                                  if len(s) >= min_word_vectors]

    # With this, we can obtain original sentences by doing sentences[original_indices[index_of_vector]]
    original_indices, sentence_sums = zip(*sentence_sums_with_indices)

    return original_indices, np.array(sentence_sums)

def w2v_sentence_means(tokenized, model):
    # define minimum number of words in the sentence that are also in the word model.
    min_word_vectors = 1

    # lowercase & split tokenized sentences
    preprocessed = [sentence.lower().split(' ')
                    for sentence in tokenized]

    # POS-tag filtering, and punctuation removal
    preprocessed = [[word.translate(str.maketrans('', '', string.punctuation))
                     for word_index, word in enumerate(sentence)]
                    for sentence_index, sentence in enumerate(preprocessed)]

    vectorized = [[model.model[word] for word in sentence
                   if word in model.model.vocab]
                  for sentence in preprocessed]

    sentence_sums_with_indices = [(index, np.mean(s, axis=0))
                                  for index, s in enumerate(vectorized)
                                  if len(s) >= min_word_vectors]

    # With this, we can obtain original sentences by doing sentences[original_indices[index_of_vector]]
    original_indices, sentence_sums = zip(*sentence_sums_with_indices)

    return original_indices, np.array(sentence_sums)


def w2v_sentence_sums_tfidf(tokenized, model, idf_weight_dict):
    # define minimum number of words in the sentence that are also in the word model.
    min_word_vectors = 1

    # lowercase & split tokenized sentences
    preprocessed = [sentence.lower().split(' ')
                    for sentence in tokenized]

    # POS-tag filtering, and punctuation removal
    preprocessed = [[word.translate(str.maketrans('', '', string.punctuation))
                     for word in sentence]
                    for sentence in preprocessed]

    # Remove OOV and non-TFIDF words
    vectorized = [[model.model[word]*idf_weight_dict[word] for word in sentence
                   if word in model.model.vocab
                   and word in idf_weight_dict]
                  for sentence in preprocessed]

    sentence_sums_with_indices = [(index, np.sum(s, axis=0))
                                  for index, s in enumerate(vectorized)
                                  if len(s) >= min_word_vectors]

    # With this, we can obtain original sentences by doing sentences[original_indices[index_of_vector]]
    original_indices, sentence_sums = zip(*sentence_sums_with_indices)

    return original_indices, np.array(sentence_sums)


def sif_embeddings(tokenized, model):
    # SIF weighting param a has default value
    a = 1e-3
    # Lowercase & split tokenized sentences
    preprocessed = [sentence.lower().split(' ')
                    for sentence in tokenized]

    # Punctuation removal
    preprocessed = [[word.translate(str.maketrans('', '', string.punctuation))
                     for word in sentence]
                    for sentence in preprocessed]

    # Remove OOV words and multiply by smooth word emission probability
    vectorized = [[model.model[word]* (a / (a + model.freq_dict[word])) for word in sentence
                   if word in model.model.vocab]
                  for sentence in preprocessed]

    sentence_means_with_indices = [(index, np.mean(s, axis=0))
                                  for index, s in enumerate(vectorized)
                                  if len(s) > 0]


    # With this, we can obtain original sentences by doing sentences[original_indices[index_of_vector]]
    original_indices, sentence_means = zip(*sentence_means_with_indices)

    # Remove first principal component
    sentence_means = np.array(sentence_means)
    sentence_means = sentence_means - sentence_means.dot(model.pc.transpose()) * model.pc

    return original_indices, sentence_means
