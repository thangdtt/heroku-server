from flask import Flask, request
from flask_restful import Resource, Api, reqparse

app = Flask(__name__)
api = Api(app)

items = []


class Item(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('price', type=float, required=True)

    def get(self, name):
        item = next(filter(lambda x: x['name'] == name, items), None)
        return {'item': item}, 200 if item else 404

    def post(self, name):
        item = next(filter(lambda x: x['name'] == name, items), None)
        if next(filter(lambda x: x['name'] == name, items), None) is not None:
            # bad request
            return {'message': 'The item with name {} is already exist'.format(name)}, 400

        data = Item.parser.parse_args()
        
        item = {'name': name, 'price': data['price']}
        items.append(item)
        return item, 201

    def delete(self, name):
        item = next(filter(lambda x: x['name'] == name, items), None)
        if item is not None:
            items.remove(item)
            return {'items': items}

    def put(self, name):
        data = Item.parser.parse_args()
        item = next(filter(lambda x: x['name'] == name, items), None)
        if item is None:
            item = {'name': name, 'price': data['price']}
            items.append(item)
        else:
            item.update(data)
        return item


class ItemList(Resource):
    def get(self):
        return {'items': items},


api.add_resource(Item, '/item/<string:name>')
api.add_resource(ItemList, '/item')

if __name__ == '__main__':
    app.run(debug=True)
