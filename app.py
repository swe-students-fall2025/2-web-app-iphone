import os

from bson import ObjectId
from dotenv import dotenv_values, load_dotenv
from flask import Flask, redirect, render_template, request
from pymongo import MongoClient

load_dotenv()

app = Flask(__name__)

config = dotenv_values()
app.config.from_mapping(config)

client = MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("MONGO_DB")]
animals = db["animals"]


@app.route("/")
def home():
    all_animals = list(animals.find())
    return render_template("home.html", animals=all_animals)


@app.route("/add", methods=["POST"])
def add_animal():
    if name := request.form.get("name"):
        animals.insert_one({"name": name})
    return redirect("/")


@app.route("/delete/<animal_id>", methods=["POST"])
def delete_animal(animal_id):
    animals.delete_one({"_id": ObjectId(animal_id)})
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)
