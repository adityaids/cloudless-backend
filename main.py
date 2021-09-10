from flask import Flask, jsonify, request
from flask_restful import Resource, Api
from flask_restful import reqparse
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from bson.json_util import dumps
import json

app = Flask(__name__)
api = Api(app)

auth_file = open('mongo-credentials.json', 'r')
creds = json.load(auth_file)
app.config['MONGO_URI'] = "mongodb://{user}:{pw}@{host}:{port}/{name}?authSource={authsrc}".format(
    user = creds['MONGO_USERNAME'], pw = creds['MONGO_PASSWORD'], host = creds['MONGO_HOST'], 
    port = creds['MONGO_PORT'], name = creds['MONGO_DBNAME'], authsrc = creds['MONGO_AUTH_SOURCE']
)
auth_file.close()

mongo = PyMongo(app)

class Promo(Resource):
    def get(self):
        query = {'on_promo': True}
        promo = list(mongo.db.product.find(query))
        for product in promo:
            merchant = mongo.db.merchant.find_one({'_id': ObjectId(product['merchant_id'])})
            product.update(merchant_name = merchant['name'])
        return json.loads(dumps(promo))

class Banner(Resource):
    def get(self):
        banner = list(mongo.db.banner.find())
        return json.loads(dumps(banner))

class Product(Resource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('identifier', type=int, location='args')
        parser.add_argument('merchant_id', type=str, location='args')
        args = parser.parse_args()
        query = {'identifier':args['identifier'], 'merchant_id':args['merchant_id']}
        product = mongo.db.product.find_one(query)
        return json.loads(dumps(product))

class Merchants(Resource):
    def get(self):
        merchants = mongo.db.merchant.find()
        return json.loads(dumps(merchants))

class Merchant(Resource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('merchant_id', type=str, location='args')
        args = parser.parse_args()
        merchant = mongo.db.merchant.find_one_or_404({'_id': ObjectId(args['merchant_id'])})
        return json.loads(dumps(merchant))


def not_found():
    message = {
        'status' : 404,
        'message' : 'Not Found' + request.url
    }
    resp = jsonify(message)
    resp.status_code = 404
    return resp


class User(Resource):
    def post(self):
        _json = request.json
        _name = _json['name']
        _email = _json['email']
        _pwd = _json['pwd']
        if _name and _email and _pwd and request.method == 'POST' :
            _hashed_password = generate_password_hash(_pwd)
            _ = mongo.db.user.insert({'name':_name, 'email':_email, 'pwd':_hashed_password})
            resp = jsonify("User added successfully")
            resp.status_code = 200
            return resp
    
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('user_id', type=str, location='args')
        args = parser.parse_args()
        user = mongo.db.user.find_one_or_404({'_id': ObjectId(args['user_id'])})
        return json.loads(dumps(user))

    def put(self):
        parser = reqparse.RequestParser()
        parser.add_argument('user_id', type=str, location='args')
        args = parser.parse_args()

        _id = args['user_id']
        _json = request.json
        _name = _json['name']
        _email = _json['email']
        _pwd = _json['pwd']

        if _name and _email and _pwd and _id and request.method == 'PUT':
            _hashed_password = generate_password_hash(_pwd)
            mongo.db.user.update_one({'_id': ObjectId(_id['$oid']) if '$oid' in _id else ObjectId(_id)}, {'$set': {'name': _name, 'email': _email, 'pwd':_hashed_password}})
            resp = jsonify("User update successfully")
            resp.status_code = 200
            return resp

        else :
            return not_found()


class Login(Resource):
    def post(self):
        _json = request.json
        _name = _json['name']
        _pwd = _json['pwd']
        print(_name)
        if _name and _pwd and request.method == 'POST' :
            user = mongo.db.user.find_one_or_404({'name': _name})
            check_password = check_password_hash(user['pwd'], _pwd)
            if check_password:           
                # resp = jsonify("Login successfully")
                # resp.status_code = 200
                return json.loads(dumps(user))
            else:
                resp = jsonify("Wrong Username or password ")
                resp.status_code = 401
                return resp

class Transaction(Resource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('user_id', type=str, location='args')
        args = parser.parse_args()
        query = {'user_id':args['merchant_id']}
        product = mongo.db.transaction.find(query)
        return json.loads(dumps(product))

    def post(self):
        _json = request.json
        _userId = _json['user_id']
        _merchantId = _json['merchant_id']
        _productName = _json['productName']
        _productImage = _json['productImage']
        _amount = _json['amount']
        _price = _json['price']
        _totalPrice = _json['total_price']
        _status = _json['status']
        if _userId and request.method == 'POST' :
            transaction = monggo.db.transaction.insert({repr(user_id): _userId, 'merchant_id': _merchantId, 'product_name': _productName, 'product_image': _productImage, 'amount': _amount, 'price': _price, 'total_price': _totalPrice, 'status': _status})
            resp = jsonify("transaction saved successfully")
            resp.status_code = 200
            return resp
        else:
            return not_found()


api.add_resource(Banner, '/banner')
api.add_resource(Product, '/product')
api.add_resource(Promo, '/promo')
api.add_resource(Merchants, '/merchants')
api.add_resource(Merchant, '/merchant')
api.add_resource(User, '/user')
api.add_resource(Login, '/login')
api.add_resource(Transaction, '/transaction')

if __name__ == '__main__':
    app.run(host='0.0.0.0')
