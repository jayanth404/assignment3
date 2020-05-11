from pymongo import MongoClient

client = MongoClient("mongodb://mongousers:27017")
db = client["usersmicroservice"]

ip_port = '127.0.0.1:80'
rides_hostname = "rides:80"