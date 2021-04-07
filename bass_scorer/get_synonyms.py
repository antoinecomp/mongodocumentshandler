import unidecode
from cleaner import pos_filtering
import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
from os.path import abspath, dirname


base_dir = dirname(dirname(abspath(__file__)))


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
        print(soup.find_all('li')[0].text.split(', '))
        return soup.find_all('li')[0].text.split(', ')
    else:
        return []


def synonymes_of(attributs):
    """
    Obtains the synonyms for a list of attributes
    :param attributs:
    :return:
    """
    synonymes = {}

    for attribut in attributs:
        if len(attribut.split(' ')) > 1:
            syns = []
            for att in attribut.split(' / '):
                attribut_unidecoded = unidecode.unidecode(att)
                print("attribut_unidecoded: ", attribut_unidecoded)
                print("pos_filtering(attribut_unidecoded): ", pos_filtering(attribut_unidecoded))
                if pos_filtering(attribut_unidecoded):
                    for syn in get_synonymes(pos_filtering(attribut_unidecoded)):
                        if pos_filtering(syn) != '':
                            syns.append(pos_filtering(syn))
            synonymes[unidecode.unidecode(attribut).lower()] = list(set(syns)) + [attribut]
        else:
            attribut_unidecoded = unidecode.unidecode(attribut)
            syns = [pos_filtering(syn) for syn in get_synonymes(attribut_unidecoded) if
                    pos_filtering(syn) != '']
            synonymes[attribut.lower()] = list(set(syns)) + [attribut]  # + [lemmatize_pos_filtering(attribut) if lemmatize_pos_filtering(attribut)]
    return synonymes


if __name__ == '__main__':
    d = {}
    df = pd.read_csv(base_dir + '\\bass_scorer\data\\adjectifs_anglais_2.csv')
    d = synonymes_of(df['Francais'])

    with open(base_dir + '\\bass_scorer\data\synonyms.json', 'w') as fp:
        json.dump(d, fp)