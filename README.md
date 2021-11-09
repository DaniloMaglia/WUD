# WUD Server
API that interacts with a Firebase Realtime Database to implement a messaging system.
WUD is an acronym and it stands for:
<ul>
<li>W: What</li>
<li>U: U</li>
<li>D: Doing</li>
</ul>
# Authentication
For authentication it uses the firebase email, password authentication system.
Whenever you want to interact with the API you have to first sign in to the signin route. The route will return a json with the token associated to your account (time limit of 1 hour). That token will be used to identify you inside the API.
# Routes
<ul>
<li> /auth/signup </li>
<li> /auth/signin </li>
<li> /user/get </li>
<li> /post_message </li>
<li> /get_message </li>
</ul>
