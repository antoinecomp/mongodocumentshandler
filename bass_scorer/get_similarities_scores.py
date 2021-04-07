from statistics import mean
import pymongo
import pandas as pd
import spacy
import numpy as np
import json

nlp = spacy.load('fr_core_news_md')


def short_comments_df(short_ratings):
    """
    transform comments of products in json format to dataframe.
    :param short_ratings: comments of products in json format.
    :return: dataframe of comments.
    :rtype: pandas.DataFrame
    """
    comments = []
    blobs = [x['ReviewText'] for x in short_ratings['Results']]
    for blob in blobs:
        comments.append(blob)
    dataframe = pd.DataFrame(comments,columns=['comments'])
    return dataframe


def get_similarities():
    client = pymongo.MongoClient(
        "mongodb+srv://test:Cloud2020@cluster0.n2hnd.mongodb.net/ifresearch?retryWrites=true&w=majority")
    collection = client.ifresearch.sephora3
    short_ratings = collection.find({}, {})  # for each of them I need "results": 1, "ReviewText":1
    client.close()

    d = {}
    for product in collection.find():
        d_product = {}
        name = product['q0']['Results'][0]['Name']
        description = product['q0']['Results'][0]['Description']  # on pourrait extraire les mots les plus intéressants
        note = product['q0']['Results'][0]['ReviewStatistics']['AverageOverallRating']
        comments = short_comments_df(product['q2'])['comments']
        similarities = []
        for comment in comments:
            # We only take the nouns and the verbs
            similarities.append(nlp(description).similarity(nlp(comment)))
        try:
            d[name] = {'similarity': mean(similarities), 'note': note}
        except:
            d[name] = {'similarity': np.nan, 'note': note}
    return d


if __name__ == '__main__':
    similarties = get_similarities()
    with open('webapp/data/similarities.json', 'w') as fp:
        json.dump(similarties, fp)
