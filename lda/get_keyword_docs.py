#coding=utf-8

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

## get stop words
dataset = []
texts_collection = []
file_path = './clean_data.csv'
with open(file_path, newline='') as csvfile:
    rows = csv.reader(csvfile)

    for row in rows:
        title = row[3]
        content = row[4]
        title_and_content = title + content

        texts_collection.append(title_and_content)
        dataset.append(row)
csvfile.close()

## split words by ckip
ws_results = ws(texts_collection)
clean_texts_collection  = []
index = 0

## filter with keywords
result_dataset = []
keywords = ['梅莉史翠普', '鐵娘子', '梅姨']
for index in range(len(ws_results)):
    doc = ws_results[index]
    for word in doc:
        if word in keywords:
            result_dataset.append(dataset[index])
            break

file_info = { 'filename': 'Streep_dataset.csv', 'dataset': result_dataset }
output_path = os.path.join(os.path.abspath(os.getcwd()), file_info['filename'])
with open(output_path, 'w', encoding='utf-8') as outfile:
    writer = csv.writer(outfile)
    field_names = ['年', '月', '日', '標題', '內容', '報社']
    writer.writerow(field_names)

    for data in file_info['dataset']:
        writer.writerow(data)
outfile.close()