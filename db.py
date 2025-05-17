from pymongo import MongoClient
import os

MONGO_URI = "mongodb+srv://vinayjain:RnnKbXa1c7s4HRt1@cluster0.mvczp9p.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client.gmail_app
users_collection = db.users
JWT_SECRET = "supersecret"
