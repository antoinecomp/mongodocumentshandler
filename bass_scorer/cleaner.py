import spacy

nlp = spacy.load('fr_core_news_md')


def pos_filtering(text):
    """
    lemmatize text and and filter on adjectives and nouns using Spacy Part-Of-Speech.
    :param text: string we need to filter.
    :return: text with only adjectives or nouns.
    :rtype: str
    """
    doc = nlp(text)
    verb_nouns = [d.text for d in doc
                  if (d.pos_ == 'ADJ' or d.pos_ == 'NOUN' or d.pos_ == "ADJWH")]
    return ' '.join([word for word in verb_nouns])