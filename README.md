# Adopt Me

## Team Members

[Xiaomin Liu](https://github.com/xl4624)
[William Chan](https://github.com/wc2184)
[Eason Huang](https://github.com/Gilgamesh605)
[Mya Pyke](https://github.com/myapyke123)
[Abdul Mendahawi](https://github.com/amendahawi)

## Product vision statement

Our Pet Adoption web application helps individuals and families find pets to adopt by connecting them with animals from local shelters all in one platform.

## User stories

[See Issues](https://github.com/swe-students-fall2025/2-web-app-iphone/issues)

## Steps necessary to run the software

Prerequisites
- Docker Desktop (recommended), or Python 3.10+ and Git

Environment
- Copy the example env and adjust values:
  ```powershell
  copy .env.example .env
  ```
  Required keys:
  ```
  MONGO_URI=mongodb://mongodb:27017/
  MONGO_DBNAME=pet_adoption
  ```

Run with Docker (quick start)
```powershell
docker compose up --build
```
App: http://localhost:5000  
Stop: `docker compose down`

Local development (without Docker)
```powershell
py -3 -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```
Update `.env` for local Mongo (or Atlas):
```
MONGO_URI=mongodb://localhost:27017/
MONGO_DBNAME=pet_adoption
```
Start:
```powershell
python app.py
# or
$env:FLASK_APP="app.py"; flask run
```

## Task boards

[Sprint Board 1](https://github.com/orgs/swe-students-fall2025/projects/26/views/1)
[Sprint Board 2](https://github.com/orgs/swe-students-fall2025/projects/71/views/1)
