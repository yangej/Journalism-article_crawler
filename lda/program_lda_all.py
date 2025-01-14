#coding=utf-8

from wordcloud import WordCloud, ImageColorGenerator
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import GridSearchCV
import numpy as np
import re
import os
import csv
from ckiptagger import WS
ws = WS("./data")

## get stop words
removed_words = []
with open('stop_word.txt') as f:
    removed_words = [line.strip() for line in f.readlines()]
f.close()

with open('stop_word_manual.txt') as f:
    [removed_words.append(line.strip()) for line in f.readlines()]
f.close()

## get dataset
dataset_name = 'clean_data.csv'
titles = []
texts_collection = []
original_dataset = []
with open(dataset_name) as f:
    title_and_content = ''
    for line in f.readlines():
        str_arr = line.split(',')

        year = str_arr[0]
        month = str_arr[1]
        date = str_arr[2]
        title = str_arr[3]
        content = str_arr[4]
        publisher = str_arr[5].strip()
        original_data = (year, month, date, title, content, publisher)
        title_and_content = title + content

        original_dataset.append(original_data)
        titles.append(title)
        texts_collection.append(title_and_content)
f.close()
collection_length = len(original_dataset)

## split words by ckip
ws_results = ws(texts_collection)
clean_texts_collection  = []
index = 0
for word_seg in ws_results:
    clean_texts_collection.append((titles[index], ' '.join([word for word in word_seg if word not in removed_words])))
    index += 1

class OutputFile:
    def __init__(self, doc_tuples, top_tuples, topics, topic_num, top_dictionary):
        self.doc_tuples = doc_tuples
        self.top_tuples = top_tuples
        self.topics = topics
        self.topic_num = topic_num
        self.top_dictionary = top_dictionary

        dir_path = ''
        if (dataset_name == 'test_articles.csv'):
            dir_path = os.path.abspath(os.getcwd()) + f'/sklearn_test_results/all_results/all_{self.topic_num}_cluster_results'
        else:
            dir_path = os.path.abspath(os.getcwd()) + f'/sklearn_results/all_results/all_{self.topic_num}_cluster_results'
        self.__dir_path = dir_path

    def create_doc_topic_file(self):
        doc_file = f'all_{self.topic_num}_by_document.csv'
        doc_path = os.path.join(self.__dir_path, doc_file)
        doc_file_exist = False

        if (os.path.exists(doc_path)):
            doc_file_exist = True

        with open(doc_path, 'w', encoding='utf-8') as outfile:
            writer = csv.writer(outfile)
            if (doc_file_exist == False):
                field_names = ['topic',  'title']
                writer.writerow(field_names)

            for doc_tuple in self.doc_tuples:
                tuple = (doc_tuple[0], doc_tuple[1])
                writer.writerow(tuple)
        outfile.close()

    def create_topic_dataset(self):
        keys = self.top_dictionary.keys()
        for key in keys:
            doc_file = f'all_{self.topic_num}_{key}_dataset.csv'
            doc_file_exist = False

            if (os.path.exists(doc_file)):
                doc_file_exist = True

            with open(doc_file, 'w', encoding='utf-8') as outfile:
                writer = csv.writer(outfile)
                if (doc_file_exist == False):
                    field_names = ['年', '月', '日', '標題', '內容', '報社']
                    writer.writerow(field_names)

                for index in self.top_dictionary[key]:
                    selected_doc = original_dataset[index]
                    writer.writerow(selected_doc)
            outfile.close()

    def create_topic_doc_file(self):
        doc_file = f'all_{self.topic_num}_by_cluster.csv'
        doc_path = os.path.join(self.__dir_path, doc_file)
        doc_file_exist = False

        if (os.path.exists(doc_path)):
            doc_file_exist = True

        with open(doc_path, 'w', encoding='utf-8') as outfile:
            writer = csv.writer(outfile)
            if (doc_file_exist == False):
                field_names = ['topic', 'features', 'count', 'title']
                writer.writerow(field_names)

            for tuple in self.top_tuples:
                writer.writerow(tuple)
        outfile.close()

    def create_files(self):
        try:
            os.makedirs(self.__dir_path)
        except Exception as ex:
            print('directory exists')

        self.create_topic_doc_file()
        self.create_topic_dataset()

year_lda = []
year_clusters = []
num_topics = [5, 6, 7]
num_feature = 20

## gather all words
all_docs = []
for doc_tuple in clean_texts_collection:
    all_docs.append(doc_tuple[1])

## create training dictionary and bag of words
cv = CountVectorizer()
cv_data = cv.fit_transform(all_docs)
cv_feature_names = cv.get_feature_names()

## create different number of topics
for topic_num in num_topics:
    lda = LatentDirichletAllocation(n_components=topic_num,
                                    learning_method='online',
                                    max_iter=1000,
                                    learning_offset=200,
                                    random_state=0,
                                    learning_decay=0.1).fit(cv_data)
    lda_components = lda.components_
    doc_topic = lda.transform(cv_data)
    ## doc_topic is the scores that the doc is assigned to each topics

    ## gather topics with features
    topics = []
    for i, topic in enumerate(lda_components):
        ## components_主題詞分佈的變體參數。
        ## 由於主題詞分發的完整條件是Dirichlet，因此components_ [i，j]可以被視為偽代碼，其表示將字j分配給主題i的次數。
        ## 它也可以被視為標準化後每個主題的單詞分佈。
        topic_features = [f"{cv_feature_names[i]}: {str(round(topic[i], 2))}" for i in topic.argsort()[:-num_feature - 1:-1]]
        topics.append(topic_features)

    ## create documents with assigned topic
    doc_tuples = []
    for i in range(collection_length):
        most_fit_topic = doc_topic[i].argmax()
        title = clean_texts_collection[i][0]

        tuple = (most_fit_topic, i)
        doc_tuples.append(tuple)

    ## create topics with belonging documents
    top_dictionary = {}
    for i in range(collection_length):
        current_doc = doc_tuples[i]
        doc_topic = current_doc[0]
        doc_index = current_doc[1]

        if top_dictionary.get(doc_topic) == None:
            top_dictionary[doc_topic] = [doc_index]
        else:
            top_dictionary[doc_topic].append(doc_index)

    top_tuples = []
    for topic_i in range(topic_num):
        features = '|'.join(topics[topic_i])

        if top_dictionary.get(topic_i) == None:
            top_tuples.append((topic_i, features, 0, []))
        else:
            doc_count = len(top_dictionary[topic_i])
            title = top_dictionary[topic_i]
            top_tuples.append((topic_i, features, doc_count, title))

    output = OutputFile(doc_tuples, top_tuples, topics, topic_num, top_dictionary)
    output.create_files()