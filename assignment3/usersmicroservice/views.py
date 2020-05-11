from flask import Flask, request, Response, jsonify
from config import db, ip_port, rides_hostname
import requests
import re

app = Flask(__name__)


@app.errorhandler(405)
def four_zero_five(e):
    increment_requests_count()
    return Response(status=405)


@app.route('/api/v1/users', methods=["PUT", "GET"])
def add_user():
    increment_requests_count()
    if request.method == "PUT":
        request_data = request.get_json(force=True)

        try:
            username = request_data["username"]
            password = request_data["password"]
        except KeyError:
            # print("Inappropriate request received")
            return Response(status=400)

        if re.match(re.compile(r'\b[0-9a-f]{40}\b'), password) is None:
            # print("Not a SHA-1 password")
            return Response(status=400)

        post_data = {"insert": [username, password], "columns": ["_id", "password"], "table": "users"}
        response = requests.post('http://' + ip_port + '/api/v1/db/write', json=post_data)

        if response.status_code == 400:
            # print("Error while inserting user to database")
            return Response(status=400)

        return Response(status=201, response='{}', mimetype='application/json')

    elif request.method == "GET":
        post_data = {"many": 1, "table": "users", "columns": ["_id"], "where": {}}
        response = requests.post('http://' + ip_port + '/api/v1/db/read', json=post_data)
        res = []
        for i in response.json():
            res.append(i['_id'])
        if not res:
            return Response(status=204)
        return jsonify(res)


@app.route('/api/v1/users/<username>', methods=["DELETE"])
def remove_user(username):
    increment_requests_count()

    post_data = {'column': '_id', 'delete': username, 'table': 'users'}
    response = requests.post('http://' + ip_port + '/api/v1/db/write', json=post_data)
    if response.status_code == 400:
        return Response(status=400)
    return jsonify({})


@app.route('/api/v1/_count', methods=["GET", "DELETE"])
def requests_count():
    if request.method == "GET":
        f = open("requests_count.txt", "r")
        res = [int(f.read())]
        f.close()
        return jsonify(res)
    elif request.method == "DELETE":
        f = open("requests_count.txt", "w")
        f.write("0")
        f.close()
        return jsonify({})


@app.route('/api/v1/db/write', methods=["POST"])
def write_to_db():
    request_data = request.get_json(force=True)

    if 'delete' in request_data:
        try:
            delete = request_data['delete']
            column = request_data['column']
            collection = request_data['table']
        except KeyError:
            # print("Inappropriate request received")
            return Response(status=400)

        try:
            query = {column: delete}
            collection = db[collection]
            x = collection.delete_one(query)
            if x.raw_result['n'] == 1:
                return Response(status=200)
            return Response(status=400)
        except:
            # print("Mongo query failed")
            return Response(status=400)

    try:
        insert = request_data['insert']
        columns = request_data['columns']
        collection = request_data['table']
    except KeyError:
        # print("Inappropriate request received")
        return Response(status=400)

    try:
        document = {}
        for i in range(len(columns)):
            document[columns[i]] = insert[i]

        collection = db[collection]
        collection.insert_one(document)
        return Response(status=201)

    except:
        return Response(status=400)


@app.route('/api/v1/db/read', methods=["POST"])
def read_from_db():
    request_data = request.get_json(force=True)
    try:
        table = request_data['table']
        columns = request_data['columns']
        where = request_data['where']
    except KeyError:
        # print("Inappropriate request received")
        return Response(status=400)

    filter = {}
    for i in columns:
        filter[i] = 1

    if 'many' in request_data:
        try:
            collection = db[table]
            res = []
            for i in collection.find(where, filter):
                res.append(i)

            return jsonify(res)
        except:
            return Response(status=400)

    try:
        collection = db[table]
        result = collection.find_one(where, filter)
        return jsonify(result)
    except:
        return Response(status=400)


@app.route('/api/v1/db/clear', methods=["POST"])
def clear_db():
    collection1 = db["users"]
    collection2 = db["rides"]
    try:
        collection1.delete_many({})
        collection2.delete_many({})
        f = open("seq.txt", "w")
        f.write("0")
        f.close()
        return Response(status=200)
    except:
        return Response(status=400)


def increment_requests_count():
    f = open("requests_count.txt", "r")
    count = int(f.read())
    f.close()
    f2 = open("requests_count.txt", "w")
    f2.write(str(count + 1))
    f2.close()


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=80)
