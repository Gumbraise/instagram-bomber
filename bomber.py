import sys
import instagrapi
import json
import random
import os
import signal
from getpass import getpass

config = []
cl = instagrapi.Client()


def login():
    while True:
        isAccount = input("Login | Do you have an account list ? (y/N): ")
        if not isAccount or isAccount != "y":
            while True:
                if openJson()['sessionId'] == "":
                    while True:
                        username = input("Login | Username: ")
                        try:
                            password = getpass(prompt="Login | Password: ")
                        except Exception as error:
                            print("Login | Error:", error)
                        try:
                            cl.login(username, password)
                            print('Login | Logged in as {}'.format(cl.username))
                            break
                        except:
                            print('Login | Bad password')
                    writeJson('sessionId', cl.sessionid)
                    print('Login | sessionId saved')
                    break
                else:
                    try:
                        cl.login_by_sessionid(openJson()['sessionId'])
                        print('Login | Logged in by sessionId')
                        break
                    except:
                        while True:
                            username = input("Login | Username: ")
                            try:
                                password = getpass(prompt="Login | Password: ")
                            except Exception as error:
                                print("Login | Error:", error)
                            try:
                                cl.login(username, password)
                                print('Login | Logged in as {}'.format(cl.username))
                                break
                            except:
                                print('Login | Bad password')
                        writeJson('sessionId', cl.sessionid)
                        print('Login | sessionId saved')
                        break
            break
        else:
            while True:
                accounts = input("Login | Path: ")
                try:
                    line = random.choice(open(accounts).readlines())
                    username, password = line.split(':')
                    print("Login | Username found: ", username)
                    cl.login(username, password)
                    break
                except:
                    print("Login | Wrong file")
            break


def start():
    clear()
    main()


def clear():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(header)


def bomber():
    clear()
    login()

    while True:
        while True:
            modeChoice = input('| Use grabbed users ? (y/N): ')
            user = ""
            if modeChoice == "y":
                user_id = openJson()['userList']
                break
            else:
                while True:
                    user = input("| Victim username: ")
                    try:
                        user_id = cl.user_info_by_username(user).pk
                        break
                    except:
                        print('Bad username')
                break

        while True:
            message = input("| Message: ")
            times = 1
            if modeChoice != "y":
                while True:
                    try:
                        times = int(input("| How many ?: "))
                        break
                    except:
                        print("Wrong number")

            # proxylist = input("Proxy list (TXT): (If you don't have proxy list press ENTER): ")
            # if accounts:
            #     proxy = random.choice(open(proxylist).readlines())
            #     api.setProxy(proxy)

            try:
                noStop = 0
                if modeChoice == "y":
                    for oneUser in user_id:
                        noStop += 1
                        cl.direct_send(message, [oneUser])
                        print("({}) {} > {}: {}".format(noStop, cl.username, oneUser, message))
                    break
                else:
                    while times > noStop:
                        noStop += 1
                        cl.direct_send(message, [user_id])
                        print("({}) {} > {}: {}".format(noStop, cl.username, user, message))
                    break

            except:
                start()


def grabUser():
    clear()
    login()
    print(grabbedMenu)

    grabChoice = int(input("| "))
    while True:
        if grabChoice == 3:
            start()
            break
        else:
            while True:
                user = input("| Grabbed username: ")
                try:
                    user_id = cl.user_info_by_username(user).pk

                    if grabChoice == 1:
                        grabFollowers = cl.user_followers(user_id)
                        listFollowers = list(grabFollowers)
                        intFollowers = list(map(int, listFollowers))
                        writeJson('userList', intFollowers)
                        print('{} followers of {} grabbed'.format(str(len(list(grabFollowers))), user))
                    if grabChoice == 2:
                        grabFollowing = cl.user_following(user_id)
                        listFollowing = list(grabFollowing)
                        intFollowing = list(map(int, listFollowing))
                        writeJson('userList', intFollowing)
                        print('{} followers of {} grabbed'.format(str(len(list(grabFollowing))), user))

                    input('Continue...')
                    clear()
                    print(grabbedMenu)
                    grabChoice = int(input("| "))
                    break
                except instagrapi.exceptions.UserNotFound:
                    print('Bad username')

                break


def usToArray(us):
    return str(len(us))


def update():
    os.system("git pull")


def main():
    print(mainMenu)
    while True:
        menuCursor = input("| ")
        try:
            if int(menuCursor) == 1:
                bomber()
            elif int(menuCursor) == 2:
                grabUser()
            elif int(menuCursor) == 3:
                update()
            elif int(menuCursor) == 4:
                sys.exit()
            else:
                print("Wrong input")
        except ValueError:
            print("Wrong input")


def writeJson(key, value):
    with open('config.json', 'r+') as jsonFile:
        data = json.load(jsonFile)
        data[key] = value
        jsonFile.seek(0)
        json.dump(data, jsonFile, indent=4)
        jsonFile.truncate()
        jsonFile.close()


def openJson():
    with open('config.json', 'r') as jsonFile:
        config = json.load(jsonFile)
        jsonFile.close()
        return config


header = """
██╗ ██████╗       ██████╗  ██████╗ ███╗   ███╗██████╗ ███████╗██████╗ 
██║██╔════╝       ██╔══██╗██╔═══██╗████╗ ████║██╔══██╗██╔════╝██╔══██╗
██║██║  ███╗█████╗██████╔╝██║   ██║██╔████╔██║██████╔╝█████╗  ██████╔╝
██║██║   ██║╚════╝██╔══██╗██║   ██║██║╚██╔╝██║██╔══██╗██╔══╝  ██╔══██╗
██║╚██████╔╝      ██████╔╝╚██████╔╝██║ ╚═╝ ██║██████╔╝███████╗██║  ██║
╚═╝ ╚═════╝       ╚═════╝  ╚═════╝ ╚═╝     ╚═╝╚═════╝ ╚══════╝╚═╝  ╚═╝
https://github.com/Gumbraise/instagram-bomber ╬ Ver. {}
""".format(openJson()['version'])

mainMenu = """
 1 | Instagram Bomber
 2 | Get User List
 3 | Update
 4 | Exit
"""

grabbedMenu = """
 1 | Grab Followers
 2 | Grab Following
 3 | Back
"""

print("Launching Instagram-Bomber...")
update()
clear()
main()
