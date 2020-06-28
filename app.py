from flask import Flask, request
from flask_restful import Resource, Api

import threading
import time

from articles import getNewsFromId, getLastId, saveArticles
from music import getMusicByCountry, crawAndSaveDB
from constance import constances
app = Flask(__name__)
api = Api(app)


class Articles(Resource):
    def get(self, id):
        items = []
        if (int(id) == 0):
            items = getNewsFromId(getLastId())
        else:
            items = getNewsFromId(int(id))
        if items is None:
            return {'message': "Can't get articles"}, 400
        return items, 200

class Music(Resource):
    def get(self, country):
        items = []
        items = getMusicByCountry(country)

        if items is None:
            return {'message': "Can't get songs"}, 400
        return items, 200

api.add_resource(Articles, '/article/<string:id>')
api.add_resource(Music, '/music/<string:country>')


def crawlArticle():
    while True:
        saveArticles()
        time.sleep(constances.TIME_BETWEEN_CRAWL)
        print("News Crawled")

@app.route('/article/run')
def crawArticleThread():
    threading.Thread(
        target=crawlArticle,
    ).start()
    return "Crawling articles"

def crawlMusic():
    while True:
        crawAndSaveDB()
        time.sleep(43200)
        print("Music Crawled")

@app.route('/music/run')
def crawMusicThread():
    threading.Thread(
        target=crawlMusic,
    ).start()
    return "Crawling music"


if __name__ == '__main__':
    app.run(debug=True)
