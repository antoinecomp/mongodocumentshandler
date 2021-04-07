import pymongo
import requests
from bs4 import BeautifulSoup
import json
import translatepy
import spacy

nlp = spacy.load('fr_core_news_md')
translator = translatepy.Translator()


def presence(words, text):
    """
    Given a text returns how many times the words are within it.
    :param words: dictionnary of words and their synonyms
    :param text: the text to investigate
    :return: a dictionnary of words and their synonyms.
    """
    if type(words) == list:
        words = [word.lower() for word in words if word != '']
        for word in words:
            if word in text:
                return 1
        return 0
    else:
        if words in text:
            return 1
        return 0


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


username = 'test'
password = 'Com.2020'


def get_synonymes(word):
    """
    Query the website that gets the synonyms.
    :param word: the word we want the synonyms of.
    :return: list of synonyms.
    :rtype: list
    """
    r = requests.get("http://www.synonymes.com/synonyme.php", params={'mot': word})
    html = r.text
    soup = BeautifulSoup(html, "html.parser")
    if len(soup.find_all('li'))>0:
        return soup.find_all('li')[0].text.split(', ')
    else:
        return []


def get_benefits(product):
    comments = [review['ReviewText'] for review in product['q2']['Results']]
    description = product['q0']['Results'][0]['Description']

    with open('./data/keywords.json') as f:
        keywords = json.load(f)
        for keyword in keywords:
            french_keyword = translator.translate(keyword, "French")
            synonymes = get_synonymes(french_keyword)

            d_product = {}
            # for every attributes
            for synonyme in synonymes:
                consumers_approved = 0
                # Are they, or their synonyms, in the comments?
                # if the attribute or it synonyms are in the description then the product has the attribut
                product_approved = presence(synonyme, description)
                for comment in comments:
                    # We only take the nouns and the verbs
                    lemmatized_comment = pos_filtering(comment)
                    # if the attribute or it synonyms are in the comments then the consumer found the attribut
                    consumers_approved += presence(synonyme, lemmatized_comment)
                # we take the proportion of people who used the attribute, but shouldn't we normalize it?
                proportion_approved = consumers_approved / len(comments)
            # we use the difference between if we found it in the description and the % of people who found it as well
            d_product[keyword] = {"claimed_benefit": product_approved, "perceived_benefit": proportion_approved}
            # d_product['TotalResults'] = product['q2']['TotalResults']
            # d_product = {k: v for k, v in sorted(d_product.items(), key=lambda item: item["perceived_benefit"])}
        return d_product


if __name__ == '__main__':
    client = pymongo.MongoClient(
        f"mongodb+srv://{username}:{password}@cluster0.n2hnd.mongodb.net/test?retryWrites=true&w=majority")
    collection = client.test.sephora_backup3
    cursor = collection.find()
    for doc in cursor:
        attributes = get_benefits(doc)
        print("attributes: ", attributes)
        doc.update({'$set': {'attributes': attributes}}, upsert=False, multi=False)
    # product = [x for x in cursor]
    client.close()


