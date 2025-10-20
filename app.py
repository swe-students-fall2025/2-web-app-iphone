import os

from bson import ObjectId
from dotenv import dotenv_values, load_dotenv
from flask import Flask, redirect, render_template, request, abort
from bson.errors import InvalidId
from pymongo import MongoClient

load_dotenv()

app = Flask(__name__)

config = dotenv_values()
app.config.from_mapping(config)

client = MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("MONGO_DB")]
animals = db["animals"]
pets_collection = animals
print("Connected to MongoDB", client, db, animals)


@app.route("/")
def home():
    all_animals = list(animals.find())
    return render_template("home.html", animals=all_animals)


@app.route("/add", methods=["POST"])
def add_animal():
    """Add a new animal document to the database."""

    name = (request.form.get("name") or "").strip()
    if not name:
        return redirect("/")

    new_animal: dict[str, object] = {"name": name}

    def _optional_text(field: str) -> str | None:
        value = request.form.get(field, "").strip()
        return value or None

    for key in ["age", "breed", "shelter", "sex", "bio", "requirements", "address"]:
        if value := _optional_text(key):
            new_animal[key] = value

    if photo_url := _optional_text("photo_url"):
        new_animal["photo_url"] = photo_url

    if distance := _optional_text("distance"):
        try:
            new_animal["distance"] = float(distance)
        except ValueError:
            new_animal["distance"] = distance

    if traits_raw := _optional_text("traits"):
        traits = [trait for trait in (t.strip() for t in traits_raw.split(",")) if trait]
        if traits:
            new_animal["traits"] = traits

    animals.insert_one(new_animal)
    return redirect("/")


@app.route("/delete/<animal_id>", methods=["POST"])
def delete_animal(animal_id):
    try:
        animals.delete_one({"_id": ObjectId(animal_id)})
    except (InvalidId, TypeError):
        abort(404)
    return redirect("/")

@app.route("/details/<animal_id>")
def details(animal_id):
    try:
        doc = animals.find_one({"_id": ObjectId(animal_id)})
    except (InvalidId, TypeError):
        abort(404)

    if not doc:
        abort(404)

    return render_template("details.html", animal=doc)


if __name__ == "__main__":
    app.run(debug=True)
