import pymongo
from cleaner import pos_filtering
import json
import os
import sys
import getpass

script_path = os.path.abspath(os.path.dirname(__file__))
synonyms_path = os.path.join(script_path, "data\synonyms.json")

# asking for your database credentials
if sys.stdin.isatty():
    print("Enter your MongoDB credentials")
    username = input("Username: ")
    password = getpass.getpass("Password: ")
else:
    username = sys.stdin.readline().rstrip()
    password = sys.stdin.readline().rstrip()


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


def get_perfumes():
    """
    Returns the claimed benefits and perceived benefit of all items.
    :return: a dictionary of the items and their features.
    :rtype: dict
    """
    try:
        client = pymongo.MongoClient(
            f"mongodb+srv://{username}:{password}@cluster0.n2hnd.mongodb.net/ifresearch?retryWrites=true&w=majority")
        collection = client.ifresearch.sephora3
        cursor = collection.find({})
        products = [x for x in cursor]
    except pymongo.errors.OperationFailure:
        print("Authentication failed")
        return

    with open(synonyms_path) as f:
        synonymes = json.load(f)

    d = {}
    for product in products:
        d_product = {}
        comments = [review['ReviewText'] for review in product['q2']['Results']]
        description = product['q0']['Results'][0]['Description']
        name = product['q0']['Results'][0]['Name']
        d_product['TotalResults'] = product['q2']['TotalResults']
        d_product['Description'] = description
        d_product['ReviewTexts'] = comments
        d_product['ImageUrl'] = product['q0']['Results'][0]['ImageUrl']
        print(name)

        # for every attributes
        for attribut in synonymes.keys():
            consumers_approved = 0
            # Are they, or their synonyms, in the comments?
            try:
                # if the attribute or it synonyms are in the description then the product has the attribut
                product_approved = presence(synonymes[attribut], description)
                for comment in comments:
                    # We only take the nouns and the verbs
                    lemmatized_comment = pos_filtering(comment)
                    # if the attribute or it synonyms are in the comments then the consumer found the attribut
                    consumers_approved += presence(synonymes[attribut], lemmatized_comment)
                # we take the proportion of people who used the attribute, but shouldn't we normalize it?
                proportion_approved = consumers_approved / len(comments)
            except IndexError:
                print("IndexError: ", attribut)
            except ZeroDivisionError:
                proportion_approved = 0
            # we use the difference between if we found it in the description and the % of people who found it as well
            d_product[attribut] = {"claimed_benefit": product_approved, "perceived_benefit": proportion_approved}
            # d_product = {k: v for k, v in sorted(d_product.items(), key=lambda item: item["perceived_benefit"])}
        client.close()
        # d_product = {k: v for k, v in sorted(d_product.items(), key=lambda item: item["perceived_benefit"])}
        d[name] = d_product
    return d


def get_perfume(name):
    """
    Computes and returns the claimed and perceived benefits proportion of a given item in its comments and description.
    :param name: the name of the perfume we want the claimed and perceived benefits of.
    :return: a dictionary with the claimed benefits and perceived benefits of the item asked.
    :rtype: dict
    """
    client = pymongo.MongoClient(
        f"mongodb+srv://{username}:{password}@cluster0.n2hnd.mongodb.net/ifresearch?retryWrites=true&w=majority")
    collection = client.ifresearch.sephora3
    cursor = collection.find({"q0.Results.Name": name})
    product = [x for x in cursor]
    comments = [review['ReviewText'] for review in product[0]['q2']['Results']]
    description = product[0]['q0']['Results'][0]['Description']

    with open('./data/synonyms.json') as f:
        synonymes = json.load(f)
        d_product = {}

        # for every attributes
        for attribut in synonymes.keys():
            consumers_approved = 0
            # Are they, or their synonyms, in the comments?
            try:
                # if the attribute or it synonyms are in the description then the product has the attribut
                product_approved = presence(synonymes[attribut], description)
                for comment in comments:
                    # We only take the nouns and the verbs
                    lemmatized_comment = pos_filtering(comment)
                    # if the attribute or it synonyms are in the comments then the consumer found the attribut
                    consumers_approved += presence(synonymes[attribut], lemmatized_comment)
                # we take the proportion of people who used the attribute, but shouldn't we normalize it?
                proportion_approved = consumers_approved / len(comments)
            except IndexError:
                print("IndexError: ", attribut)
            # we use the difference between if we found it in the description and the % of people who found it as well
            d_product[attribut] = {"claimed_benefit": product_approved, "perceived_benefit": proportion_approved}
            d_product['TotalResults'] = product['q2']['TotalResults']
            d_product = {k: v for k, v in sorted(d_product.items(), key=lambda item: item["perceived_benefit"])}
        client.close()
        return d_product


if __name__ == '__main__':
    products = get_perfumes()
    with open('webapp/data/products.json', 'w') as fp:
        json.dump(products, fp, indent=2)
