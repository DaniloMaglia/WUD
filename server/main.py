import json
from firebase_admin.exceptions import FirebaseError
from flask import request, Flask
from flask.wrappers import Response
from flask_cors import CORS, cross_origin
from message import Message
from db_driver import APIException, FirebaseConnection
from db_driver import User
from firebase_admin.exceptions import FirebaseError

INVALID_TOKEN = {
    "code": "invalid_token",
    "message": "Invalid token. Token validity check failed, check if the token is not expired",
}

INVALID_USER = {
    "code": "invalid_user",
    "message": "Invalid user. The associated username has not been found in the database"
}

INVALID_DEST = {
    "code": "invalid_dest",
    "message": "The destinatary of the message is not valid, please check the unique id",
}

INVALID_PARAMETER = {
    "code": "invalid_parameter",
    "message": "You sent invalid parameter to the API, check carefully to see where is the error",
}

USER_EXISTS = {
    "code": "user_exists",
    "message": "The user (name) you sent is already being used",
}

EMAIL_EXISTS = {
    "code": "email_exists",
    "message": "The user (email) you sent is already being used",
}

INVALID_LOGIN = {
    "code": "invalid_login",
    "message": "Invalid email or password"
}

MISSING_AUTHORIZATION = {
    "code": "missing_authorization",
    "message": "Missing Authorization header containing the token"
}

app = Flask(__name__)
cors = CORS(app)
app.config["DEBUG"] = True

fb = FirebaseConnection(
    "./res/key/key.json",
    "https://whatudoing-default-rtdb.europe-west1.firebasedatabase.app/",
)


@app.route("/post_message", methods=["POST"])
# Route per inviare un messaggio ad un utente.
# Come body prende un json con i seguenti parametri:
#   dest   = id dell'utente a cui è destinato il messaggio
#   msg    = il messaggio inviato
# Come header accetta i seguenti parametri:
#   Authorization  = token della persona che vuole inviare il messaggio
# Il messaggio verrà messo tra i "pending_message" e potrà
# essere preso solo quando il destinatario richiederà i
# propri messaggi.
@cross_origin()
def post_message():
    try:
        token = request.headers["Authorization"]
    except KeyError:
        return Response(json.dumps(MISSING_AUTHORIZATION), status=400)
    dest = request.json["dest"]
    msg = request.json["msg"]
    try:
        user = User.get_user_by_token(fb, token)
    except APIException:
        return INVALID_TOKEN
    try:
        user.send_message(fb, dest, msg)
        return {"code": "success", "message": "Message sent successfully"}
    except User.UserException:
        return INVALID_DEST


@app.route("/get_message", methods=["POST"])
# Route per leggere i messaggi ricevuti.
# Come body la richiesta non prende nulla.
# Come header la richiesta accetta i seguenti parametri:
#   Authorization = token che identifica la sessione di un utente (vedere signin)
# Verrà ritornato il messaggio con il seguente formato
# {
#   src: [src],
#   msg: [msg]
# }
# In caso ci siano più messaggi verrà ritornata una lista.
@cross_origin()
def get_message():
    print(request.json)
    try:
        token = request.headers["Authorization"]
    except KeyError:
        return Response(json.dumps(MISSING_AUTHORIZATION), status=400)
    try:
        user = User.get_user_by_token(fb, token)
        pending_messages = user.get_pending_messages(fb)
        if pending_messages is not None:
            return pending_messages
        else:
            return INVALID_DEST
    except APIException:
        return INVALID_TOKEN


@app.route("/auth/signup", methods=["POST"])
# Route per aggiungere un utente alla piattaforma
# Utilizza il sistema di autenticazione di Firebase
# Come body prende un JSON con i seguenti parametri:
#   username = username dell'utente
#   email = email dell'utente
#   password = password in chiaro dell'utente
# Restituisce un messaggio con il seguente formato:
# {
#   code: "success"
#   message: "User created successfully"
# }
@cross_origin()
def signup():
    username = request.json["username"]
    email = request.json["email"]
    password = request.json["password"]
    
    try:
        User.sign_up(fb, username, email, password)
        return {"code": "success", "message": "User created successfully"}
    except User.UserException:
        return USER_EXISTS
    except FirebaseError:
        return EMAIL_EXISTS


@app.route("/auth/signin", methods=["POST"])
# Route per eseguire l'accesso all'API.
# Ritorna un token che potrà essere utilizzato successivamente
# per identificarsi all'interno dell'API.
# Come body richiede un JSON con i seguenti paramentri:
#   email: [email],
#   password: [password]
# Verrà restituito un messaggio con il seguente formato
# {
#   code: "success",
#   message: "User signed in successfully",
#   token: [token]
# }
@cross_origin()
def signin():
    email = request.json["email"]
    password = request.json["password"]
    try:
        token = User.sign_in(email, password)
        return {
            "code": "success",
            "message": "User signed in successfully",
            "token": token,
        }
    except APIException:
        return INVALID_PARAMETER
    except User.UserException:
        return INVALID_LOGIN


@app.route("/user/get", methods=["POST"])
# Route per prendere i dati di un utente
# Come body la richiesta non prende nulla.
# Come header la richiesta accetta i seguenti parametri:
#   Authorization = token che identifica la sessione di un utente (vedere signin)
# Verrà restituito un messaggio con il seguente formato
# {
#   code: "success",
#   message: "User retrieved successfully",
#   user: {
#       username: [username],
#       email: [email]
#   }
# }
@cross_origin()
def get_user():
    try:
        token = request.headers["Authorization"]
    except KeyError:
        return Response(json.dumps(MISSING_AUTHORIZATION), status=400)
    try:
        user = User.get_user_by_token(fb, token)
        return {
            "code": "success",
            "message": "User retrieved sucessfully",
            "user": user.__dict__(),
        }
    except APIException:
        return INVALID_TOKEN

@app.route("/user/get_by_username", methods=["POST"])
# Route per prendere i dati di un utente
# Come body richiede un JSON con i seguenti parametri:
#   username = username dell'utente da cercare
# Verrà restituito un messaggio con il seguente formato
# {
#   code: "success",
#   message: "User retrieved successfully",
#   user: {
#       username: [username],
#       email: [email]
#   }
# }
@cross_origin()
def get_user_by_username():
    username = request.json["username"]
    try:
        user = User.get_user_by_username(fb, username)
        return {
            "code": "success",
            "message": "User retrieved sucessfully",
            "user": user.__dict__(),
        }
    except APIException:
        return INVALID_USER
    


def main():
    app.run(host="0.0.0.0", port=42069)


if __name__ == "__main__":
    main()
