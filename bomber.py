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
try:
    from InstagramAPI import InstagramAPI
    import time
    import requests
    import json
    import random
    import sys
    import getpass

    while True:
        try:
            nostop = 0

            while True:
                accounts = input("Put your Instagram accounts list here (if there is no file just press ENTER): ")
                if not accounts:
                    username = input("Put your IG Username then press ENTER: ")
                    # password = input("Put your IG Password then press ENTER: ")
                    try: 
                        password = getpass.getpass(prompt = "Put your IG Password then press ENTER: ") 
                    except Exception as error: 
                        print("Error:", error) 
                    else: 
                        print("Got Password. Attempting to login.")
                    api = InstagramAPI(username, password)
                    api.login()
                    break

                else:
                    try:
                        line = random.choice(open(accounts).readlines())
                        username, password = line.split(':')
                        print ("Username found: ", username)
                        print ("Password found: ", password)
                        api = InstagramAPI(username, password)
                        api.login()
                        break

                    except:
                        print ("Wrong file")

            while True:
                try:
                    user = input("Enter the victim's IG Username: ")
                    try:
                        response = requests.get("https://www.instagram.com/"+user+"/?__a=1")
                        respJSON = response.json()
                        user_id = str( respJSON['graphql'].get("user").get("id") )
                    except:
                        print ("Unknown victim's username")
                        print ("Program will now terminate. Kindly identify victim account.")
                        exit(0)

                    while True:
                        try:
                            nostop = 0
                            message = input("Put the message you want the software send and press ENTER: ")

                            while True:
                                try:
                                    times = int(input("How many messages do you want to send? "))
                                    break
                                except:
                                    print ("Wrong number")
                            
                            proxylist = input("Proxy list (TXT): (If you don't have proxy list press ENTER): ")
                            if 'txt' in proxylist:
                                proxy = random.choice(open(proxylist).readlines())
                                api.setProxy(proxy)
                            while times > nostop:
                                nostop = nostop + 1
                                api.sendMessage(user_id,message)
                                print(nostop, ">> Sent to", user, ": ", message)
                        except KeyboardInterrupt:
                            print ('\n')
                            break
                except KeyboardInterrupt:
                    print ('\n')
                    break
        except KeyboardInterrupt:
            print ('\nSee you soon :)')
            break
except:
    sys.exit('\nA critical error happened. Please make sure that you executed all commands properly and relaunch the program.')
