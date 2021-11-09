import firebase_admin
import firebase_admin.db
import firebase_admin.auth
from firebase_admin.exceptions import FirebaseError
from firebase_admin.auth import (
    InvalidIdTokenError,
    ExpiredIdTokenError,
    RevokedIdTokenError,
    UserDisabledError,
)
from message import Message
import os
import requests
import json

FIREBASE_WEB_API_KEY = os.environ.get("FIREBASE_WEB_API_KEY")
REST_API_URL = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"


class APIException(Exception):
    pass


class FirebaseConnection:

    reference = None
    url = None

    def __init__(self, credentials: str, url: str):
        self.url = url
        cred = firebase_admin.credentials.Certificate(credentials)
        firebase_admin.initialize_app(cred)
        self.reference = firebase_admin.db.reference(path="/", url=self.url)

    # Metodo privato per cambiare reference di Firebase
    def __change_reference(self, reference: str):
        self.reference = firebase_admin.db.reference(path=reference, url=self.url)

    def set(self, item: dict, reference: str = "/"):
        self.__change_reference(reference)
        self.reference.set(item)

    def push(self, item: dict, reference: str = "/"):
        self.__change_reference(reference)
        self.reference.push(item)

    def update(self, item: dict, reference: str = "/"):
        self.__change_reference(reference)
        self.reference.update(item)

    def get(self, reference: str = "/"):
        self.__change_reference(reference)
        fetched_item = self.reference.get()
        return fetched_item

    class DatabaseException(Exception):
        pass


class User:

    user_record = None
    username = None

    def __init__(self, user_record: firebase_admin.auth.UserRecord, username: str):
        self.user_record = user_record
        self.username = username

    # -----------------------METODI STATICI-----------------------
    @staticmethod
    def sign_up(fb: FirebaseConnection, username: str, email: str, password: str):
        if username is None or email is None or password is None:
            raise APIException("Invalid parameter")
        try:
            user_record = firebase_admin.auth.create_user(
                email=email, password=password
            )
            user = User(user_record, username)
        except FirebaseError as e:
            raise e
        if User.exists(fb, username=username):
            raise User.UserException("Username already used")
        fb.update(user.__dict__(), reference="/Users/")
        fb.update({user.username: user.user_record.uid},reference='/Usernames/')

    @staticmethod
    def sign_in(email: str, password: str):
        if email is None or password is None or email == "" or password == "":
            raise APIException("Invalid Parameters")
        user_info = json.dumps(
            {"email": email, "password": password, "returnSecureToken": True}
        )
        r = requests.post(
            REST_API_URL, params={"key": FIREBASE_WEB_API_KEY}, data=user_info
        ).json()
        if 'error' in r.keys():
            raise User.UserException("Invalid email or password")
        return r["idToken"]

    @staticmethod
    def get_user(fb:FirebaseConnection, uid: str):
        user = firebase_admin.auth.get_user(uid)
        user_data = fb.get(reference=f"Users/{uid}")
        return User(user, user_data["username"])

    @staticmethod
    def get_user_by_token(fb: FirebaseConnection, token: str):
        try:
            uid = firebase_admin.auth.verify_id_token(token)["uid"]
            return User.get_user(fb, uid)
        except (
            InvalidIdTokenError,
            ExpiredIdTokenError,
            RevokedIdTokenError,
            UserDisabledError,
        ):
            raise APIException("Invalid token")
        

    def get_user_by_username(fb: FirebaseConnection, username: str):
        if User.exists(fb, username=username):
            uid = fb.get(reference=f"Usernames/{username}")
            return User.get_user(fb, uid)
        else:
            raise APIException("User does not exists")

    @staticmethod
    def exists(fb: FirebaseConnection, uid: str = None, username: str = None) -> bool:
        if uid is not None:
            return fb.get(reference=f"/Users/{uid}/") is not None
        elif username is not None:
            return fb.get(reference=f"/Usernames/{username}") is not None
        return False
    # ----------------------- METODI -----------------------
    def send_message(self, fb: FirebaseConnection, uid_dest: str, content: str):
        if User.exists(fb, uid_dest):
            message = Message(self.user_record.uid, content)
            fb.push(
                message.__dict__(), reference=f"/Users/{uid_dest}/pending_messages/"
            )
        else:
            raise User.UserException("Invalid user unique id")

    def get_pending_messages(self, fb: FirebaseConnection):
        return fb.get(f"/Users/{self.user_record.uid}/pending_messages/")

    def __dict__(self):
        return {
            self.user_record.uid: {
                "username": self.username,
                "email": self.user_record.email,
            }
        }

    class UserException(Exception):
        pass
