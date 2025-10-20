import os

from bson import ObjectId
from bson.errors import InvalidId
from dotenv import dotenv_values, load_dotenv
from flask import Flask, abort, jsonify, redirect, render_template, request
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


def _optional_text_value(raw_value: object) -> str | None:
    """Return stripped string content or None when empty."""
    if raw_value is None:
        return None
    if not isinstance(raw_value, str):
        raw_value = str(raw_value)
    value = raw_value.strip()
    return value or None


def _coerce_float(value: str) -> float | str:
    """Attempt to convert a numeric string to float, otherwise return original string."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return value


@app.route("/")
def home():
    all_animals = list(pets_collection.find())
    return render_template("home.html", animals=all_animals)


@app.route("/add", methods=["GET", "POST"])
def add_animal():
    """Add a new animal document to the database."""

    if request.method == "GET":
        return render_template("add.html")

    name = _optional_text_value(request.form.get("name"))
    if not name:
        return redirect("/")

    new_animal: dict[str, object] = {"name": name}

    def _form_value(field: str) -> str | None:
        return _optional_text_value(request.form.get(field))

    for key in ["age", "breed", "shelter", "sex", "bio", "requirements", "address"]:
        if value := _form_value(key):
            new_animal[key] = value

    if photo_url := _form_value("photo_url"):
        new_animal["photo_url"] = photo_url

    if distance := _form_value("distance"):
        new_animal["distance"] = _coerce_float(distance)

    if traits_raw := _form_value("traits"):
        traits = [trait for trait in (t.strip() for t in traits_raw.split(",")) if trait]
        if traits:
            new_animal["traits"] = traits

    pets_collection.insert_one(new_animal)
    return redirect("/")


@app.route("/add_pet", methods=["POST"])
def add_pet():
    """Add a new pet via JSON payload (used by add.html fetch form)."""

    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return jsonify({"error": "Invalid JSON payload"}), 400

    name = _optional_text_value(payload.get("name"))
    if not name:
        return jsonify({"error": "Pet name is required"}), 400

    new_pet: dict[str, object] = {"name": name}

    field_mappings = {
        "species": "species",
        "breed": "breed",
        "age": "age",
        "gender": "sex",
        "size": "size",
        "color": "color",
        "photo_url": "photo_url",
        "description": "bio",
        "shelter": "shelter",
        "requirements": "requirements",
        "address": "address",
    }

    for source_field, target_field in field_mappings.items():
        if (value := _optional_text_value(payload.get(source_field))) is not None:
            new_pet[target_field] = value

    if (distance_raw := _optional_text_value(payload.get("distance"))) is not None:
        new_pet["distance"] = _coerce_float(distance_raw)

    if traits_raw := _optional_text_value(payload.get("traits")):
        traits = [trait for trait in (t.strip() for t in traits_raw.split(",")) if trait]
        if traits:
            new_pet["traits"] = traits

    result = pets_collection.insert_one(new_pet)
    return jsonify({"id": str(result.inserted_id)}), 201


@app.route("/delete", methods=["GET"])
def delete_page():
    """Render the delete page with the current list of pets."""

    all_animals = list(pets_collection.find())
    return render_template("delete.html", animals=all_animals)


@app.route("/delete/<animal_id>", methods=["POST"])
def delete_animal(animal_id):
    try:
        pets_collection.delete_one({"_id": ObjectId(animal_id)})
    except (InvalidId, TypeError):
        abort(404)
    return redirect("/")

@app.route("/details/<animal_id>")
def details(animal_id):
    try:
        doc = pets_collection.find_one({"_id": ObjectId(animal_id)})
    except (InvalidId, TypeError):
        abort(404)

    if not doc:
        abort(404)

    return render_template("details.html", animal=doc)


if __name__ == "__main__":
    app.run(debug=True)
