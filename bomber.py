"""
  ▄████  █    ██  ███▄ ▄███▓ ▄▄▄▄    ██▀███   ▄▄▄       ██▓  ██████ ▓█████ 
 ██▒ ▀█▒ ██  ▓██▒▓██▒▀█▀ ██▒▓█████▄ ▓██ ▒ ██▒▒████▄    ▓██▒▒██    ▒ ▓█   ▀ 
▒██░▄▄▄░▓██  ▒██░▓██    ▓██░▒██▒ ▄██▓██ ░▄█ ▒▒██  ▀█▄  ▒██▒░ ▓██▄   ▒███   
░▓█  ██▓▓▓█  ░██░▒██    ▒██ ▒██░█▀  ▒██▀▀█▄  ░██▄▄▄▄██ ░██░  ▒   ██▒▒▓█  ▄ 
░▒▓███▀▒▒▒█████▓ ▒██▒   ░██▒░▓█  ▀█▓░██▓ ▒██▒ ▓█   ▓██▒░██░▒██████▒▒░▒████▒
 ░▒   ▒ ░▒▓▒ ▒ ▒ ░ ▒░   ░  ░░▒▓███▀▒░ ▒▓ ░▒▓░ ▒▒   ▓▒█░░▓  ▒ ▒▓▒ ▒ ░░░ ▒░ ░
  ░   ░ ░░▒░ ░ ░ ░  ░      ░▒░▒   ░   ░▒ ░ ▒░  ▒   ▒▒ ░ ▒ ░░ ░▒  ░ ░ ░ ░  ░
░ ░   ░  ░░░ ░ ░ ░      ░    ░    ░   ░░   ░   ░   ▒    ▒ ░░  ░  ░     ░   
      ░    ░            ░    ░         ░           ░  ░ ░        ░     ░  ░
                                  ░                                        
"""
from InstagramAPI import InstagramAPI
import time
import requests
import json

nostop = 0

accounts = input("Put your Instagram accounts list here (if there is no file just press ENTER): ")

if not accounts:
    username = input("Put your IG Username then press ENTER: ")
    password = input("Put your IG Password then press ENTER: ")
    api = InstagramAPI(username, password)
    api.login()
    istimes = 0
else:
    f = open(accounts, 'r')
    NumberOfLine = 0
    for line in f:
        NumberOfLine += 1
    username, password = line.split(':')
    print ("Username found: ", username)
    print ("Password found: ", password)
    api = InstagramAPI(username, password)
    api.login()
    istimes = 1

user = input("Enter the victim's IG Username then press ENTER: ")


url = "https://www.instagram.com/web/search/topsearch/?context=blended&query="+user+"&rank_token=0.3953592318270893&count=1"
response = requests.get(url)
respJSON = response.json()
user_id = str( respJSON['users'][0].get("user").get("pk") )

message = input("Put the message you want the software send and press ENTER: ")

if istimes == 0:
    times = int(input("How many messages do you want to send? "))
elif istimes == 1:
    times = NumberOfLine

print("You are gonna STRESS", times,"times", user_id, "with the message: ", message, ".")
input("Are you sure?")

while times > nostop:
    nostop = nostop + 1
    api.sendMessage(user_id,message)
    print(nostop, ">> Sent to", user, ": ", message)