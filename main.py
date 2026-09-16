import requests #For making API calls
from dotenv import load_dotenv #For setting environment
load_dotenv()
import os #For accessing environment variables
import secrets #For creating code verifier and state
import hashlib #For SHA256 hashing
import base64 #For encoding
from urllib.parse import urlencode
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import webbrowser
import json
def authentication():
    code_verifier=secrets.token_urlsafe(64)
    state=secrets.token_urlsafe(32)
    class CallbackHandler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            pass
        def do_GET(self):
            # print("Recieved a request!")
            # print("Path:",self.path)
            parsed_url=urlparse(self.path)
            if (parsed_url.path !="/callback"):  #This ensures only the path /callback is taken
                self.send_response(404) #Response code to send back
                self.end_headers()
                self.wfile.write(b"Not Found")
                return
            query_parameters=parse_qs(parsed_url.query)
            if "code" not in query_parameters:  #To handle empty parameters : Checks whether the dictionary contains a code key
                self.send_response(400) 
                self.end_headers()
                self.wfile.write(b"Authorization code missing")
                return
            if "state" not in query_parameters:  #To handle empty parameters : Checks whether the dictionary contains a code key
                            self.send_response(400) 
                            self.end_headers()
                            self.wfile.write(b"State code is missing")
                            return
            nonlocal authorization_code # nonlocal scope is inside the enclosing function
            authorization_code=query_parameters["code"][0]
            nonlocal cstate
            cstate=query_parameters["state"][0]
            # print("Authorization code: ",authorization_code)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Authorization successful!")
    client_id=os.environ.get("SPOTIFY_CLIENT_ID")
    redirect_uri=os.environ.get("SPOTIFY_REDIRECT_URI")
    hashed=hashlib.sha256(code_verifier.encode()).digest()
    code_challenge=base64.urlsafe_b64encode(hashed).decode().rstrip("=")
    params =  {
      "response_type": 'code',
      "client_id": client_id,
      "code_challenge_method": 'S256',
      "code_challenge": code_challenge,
      "redirect_uri":redirect_uri,
      "scope":"user-top-read user-read-recently-played",
      "state":state
    }
    server=HTTPServer(("127.0.0.1",8888),CallbackHandler)
    authorization_url=("https://accounts.spotify.com/authorize?"+urlencode(params))
    authorization_code = None
    cstate=None
    webbrowser.open(authorization_url)
    server.handle_request()
    if authorization_code==None:
         print("Authorization failed!")
         exit()
    if state!=cstate:
        print("State is not matching!")
        exit()
    #Getting the access token using POST Requests
    token_url="https://accounts.spotify.com/api/token"
    data={
        "client_id":client_id,
        "grant_type":"authorization_code",
        "code":authorization_code,
        "redirect_uri":redirect_uri,
        "code_verifier":code_verifier
    }
    response=requests.post(token_url,data=data)
    response_code=response.status_code
    if response_code==200:
        token_data=response.json()
        access_token=token_data["access_token"]
        refresh_token=token_data["refresh_token"]
        return access_token,refresh_token
    else:
        print("Error getting token, Response code : ",response_code)
        print(response.json())
        exit()

def refreshAccessToken(refresh_token):
     client_id=os.environ.get("SPOTIFY_CLIENT_ID")
     token_url="https://accounts.spotify.com/api/token"
     data={
          "client_id":client_id,
          "grant_type":"refresh_token",
          "refresh_token":refresh_token
     }
     response=requests.post(token_url,data=data)
     if response.status_code==200:
         access_token=response.json()['access_token']
         return access_token
     else:
          print("Error refreshing access token: ",response.status_code)
          return None
def getTimeRange():
    print("What time range should be conisdered?(Choose 1,2 or 3)")
    print("1.Short Term\n2.Medium Term\n3.Long Term")
    term=int(input())
    if (term==1):
        term="short_term"
    elif term==2:
        term="medium_term"
    elif term==3:
        term="long_term"
    else:
        print("Invalid Input. Enter a valid number!")
        term=getTimeRange()
    return term

def saveRefreshToken(refresh_token):
     data={
          "refresh_token":refresh_token
     }
     with open("session.json","w") as f:
          json.dump(data,f,indent=2)
def loadRefreshToken():
     try:
          with open("session.json","r") as f:
               data=json.load(f)
          try:
               token=data["refresh_token"]
               return token
          except KeyError:
               return None
     except FileNotFoundError:
          return None
def destroyRefreshToken():
     data={}
     with open("session.json","w") as f:
          json.dump(data,f,indent=2)

def loadingScreen():
    print("Please authenticate yourself in Spotify to continue using this app!")
    print("Enter 1 to continue or anything else to exit...")
    try:
        choice=int(input())
        if choice!=1:
            exit()
    except ValueError:
        exit()
    access_token,refresh_token=authentication()  #Getting access and refresh token
    saveRefreshToken(refresh_token)
    return access_token,refresh_token

def topArtists(headers):
    print("Enter number of top artists you would like to see : ")
    x=int(input())
    term=getTimeRange()
    parameters={
    "limit":x,
    "time_range":term
    }
    response=requests.get("https://api.spotify.com/v1/me/top/artists",headers=headers,params=parameters)
    if response.status_code==200:
        user_data=response.json()
        artists=user_data['items']
        print("Here are your top",x,"artists: \n")
        for artist in artists:
            print(artist['name'])
    else:
        print("Error getting profile: ",response.status_code)
        print(response.json())


def topTracks(headers):
        print("Enter number of your top tracks you'd like to see : ")
        x=int(input())
        term=getTimeRange()
        parameters={
        "limit":x,
        "time_range":term
        }
        response=requests.get("https://api.spotify.com/v1/me/top/tracks",headers=headers,params=parameters)
        if response.status_code==200:
            user_data=response.json()
            tracks=user_data['items']
            print("Here are your top",x,"tracks: \n")
            for track in tracks:
                print(track['name']," : ",track['artists'][0]['name'])
        else:
            print("Error getting profile: ",response.status_code)
            print(response.json())


def recentlyPlayed(headers):
    parameters={
          "limit":10
    }
    response=requests.get("https://api.spotify.com/v1/me/player/recently-played",headers=headers,params=parameters)
    data=response.json()
    status_code=response.status_code
    if status_code==200:   
        items=data["items"]
        print("\nYour recently played tracks : ")
        for item in items:
            print(item["track"]["name"])
    else:
         print("Error getting recently played tracks. Status code:",status_code)
         exit()

refresh_token=loadRefreshToken()
if refresh_token:
    access_token=refreshAccessToken(refresh_token)
    if not access_token:
         access_token,refresh_token=loadingScreen()
else:
    access_token,refresh_token=loadingScreen()
headers={"Authorization":f"Bearer {access_token}"}
#Welcome note
response=requests.get("https://api.spotify.com/v1/me",headers=headers)
print("Welcome!",response.json()["display_name"])
while True:
    print("Choose what you would like to see :) ")
    print("1. Find your top artists :")
    print("2. Find your top tracks :")
    print("3. Get your recently played tracks : ")
    print("4. To logout of the app and exit")
    print("5. To exit the app")
    try:
         k=int(input())
    except ValueError:
         print("Input should be a number!")
         continue
    if k==1:
        topArtists(headers)
    elif k==2:
        topTracks(headers)
    elif k==3:
        recentlyPlayed(headers)
    elif k==4: #Will add once we set up refresh token and session persistance
         destroyRefreshToken()
         print("Good Bye! :)")
         exit()
    elif k==5:
         print("Good Bye! :) ")
         exit()
    else:
        print("Invalid Input!")