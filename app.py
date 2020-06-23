from flask import Flask, request
from flask_restful import Resource, Api

import threading
import time

import articles
import constance
app = Flask(__name__)
api = Api(app)


class Articles(Resource):
    def get(self, id):
        items = []
        if (int(id) == 0):
            items = articles.getNewsFromId(articles.getLastId())
        else:
            items = articles.getNewsFromId(int(id))
        if items is None:
            return {'message': "Can't get articles"}, 400
        return items, 200
        # return {'number of article': len(items), 'articles': items}, 200


api.add_resource(Articles, '/article/<string:id>')


def crawlData():
    while True:
        articles.saveArticles()
        time.sleep(constance.TIME_BETWEEN_CRAWL)


@app.route('/run')
def craw():
    threading.Thread(
        target=crawlData,
    ).start()
    return "Crawling"


if __name__ == '__main__':
    app.run(debug=True, threaded=True)
