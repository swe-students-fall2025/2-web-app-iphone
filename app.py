import os

from bson import ObjectId
from bson.errors import InvalidId
from dotenv import dotenv_values, load_dotenv
from flask import Flask, abort, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from pymongo import MongoClient

load_dotenv()

app = Flask(__name__)

config = dotenv_values()
app.config.from_mapping(config)
app.config.setdefault("SECRET_KEY", os.environ.get("SECRET_KEY", "dev-secret-key-change-me"))

client = MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("MONGO_DB")]
animals = db["animals"]
pets_collection = animals
users_collection = db["users"]
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
        if "user_id" not in session:
            return redirect(url_for("login"))
        return render_template("add.html")

    name = _optional_text_value(request.form.get("name"))
    if "user_id" not in session:
        return redirect(url_for("login"))
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

    if "user_id" not in session:
        return jsonify({"success": False, "message": "Login required."}), 401

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

    if "user_id" not in session:
        return redirect(url_for("login"))
    all_animals = list(pets_collection.find())
    return render_template("delete.html", animals=all_animals)


@app.route("/delete/<animal_id>", methods=["POST"])
def delete_animal(animal_id):
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Login required."}), 401
    try:
        pets_collection.delete_one({"_id": ObjectId(animal_id)})
    except (InvalidId, TypeError):
        abort(404)
    # If the client expects HTML (e.g., standard form submit), redirect home.
    if request.accept_mimetypes.accept_html and not request.accept_mimetypes.accept_json:
        return redirect("/")
    # Otherwise, return JSON for fetch/XHR callers.
    return jsonify({"success": True})

@app.route("/details/<animal_id>")
def details(animal_id):
    try:
        doc = pets_collection.find_one({"_id": ObjectId(animal_id)})
    except (InvalidId, TypeError):
        abort(404)

    if not doc:
        abort(404)

    return render_template("details.html", animal=doc)


@app.route("/search")
def search_redirect():
    # Simple placeholder: reuse home for now
    return redirect(url_for("home"))


# --- Authentication routes ---

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    username = _optional_text_value(request.form.get("username"))
    password = _optional_text_value(request.form.get("password"))

    if not username or not password:
        return jsonify({"success": False, "message": "Username and password are required."}), 400

    user = users_collection.find_one({"username": username})
    if not user or not check_password_hash(user.get("password_hash", ""), password):
        return jsonify({"success": False, "message": "Invalid username or password."}), 401

    session["user_id"] = str(user.get("_id"))
    session["username"] = user.get("username")
    return jsonify({"success": True})


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("signup.html")

    username = _optional_text_value(request.form.get("username"))
    password = _optional_text_value(request.form.get("password"))

    if not username or not password:
        return jsonify({"success": False, "message": "Username and password are required."}), 400

    if len(username) < 3:
        return jsonify({"success": False, "message": "Username must be at least 3 characters."}), 400
    if len(password) < 8:
        return jsonify({"success": False, "message": "Password must be at least 8 characters."}), 400

    existing = users_collection.find_one({"username": username})
    if existing:
        return jsonify({"success": False, "message": "Username already exists."}), 409

    password_hash = generate_password_hash(password)
    result = users_collection.insert_one({
        "username": username,
        "password_hash": password_hash,
    })

    return jsonify({"success": True, "message": "Account created.", "id": str(result.inserted_id)})


@app.route("/logout", methods=["POST", "GET"])
def logout():
    session.clear()
    if request.method == "GET":
        return redirect(url_for("home"))
    return jsonify({"success": True})
@app.route("/edit/<animal_id>")
def edit_animal(animal_id):
    """Display the edit form for an animal."""
    try:
        doc = animals.find_one({"_id": ObjectId(animal_id)})
    except (InvalidId, TypeError):
        abort(404)

    if not doc:
        abort(404)

    return render_template("edit.html", animal=doc)


@app.route("/update/<animal_id>", methods=["POST"])
def update_animal(animal_id):
    """Update an existing animal document in the database."""
    try:
        object_id = ObjectId(animal_id)
    except (InvalidId, TypeError):
        abort(404)

    name = (request.form.get("name") or "").strip()
    if not name:
        return redirect(f"/edit/{animal_id}")

    updated_animal: dict[str, object] = {"name": name}

    def _optional_text(field: str) -> str | None:
        value = request.form.get(field, "").strip()
        return value or None

    for key in ["age", "breed", "shelter", "sex", "bio", "requirements", "address"]:
        if value := _optional_text(key):
            updated_animal[key] = value

    if photo_url := _optional_text("photo_url"):
        updated_animal["photo_url"] = photo_url

    if distance := _optional_text("distance"):
        try:
            updated_animal["distance"] = float(distance)
        except ValueError:
            updated_animal["distance"] = distance

    if traits_raw := _optional_text("traits"):
        traits = [trait for trait in (t.strip() for t in traits_raw.split(",")) if trait]
        if traits:
            updated_animal["traits"] = traits

    animals.update_one({"_id": object_id}, {"$set": updated_animal})
    return redirect(f"/details/{animal_id}")


if __name__ == "__main__":
    app.run(debug=True)
