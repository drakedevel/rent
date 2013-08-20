import getpass
import rent.main as rent

def main():
    rent.script()
    username = raw_input("Username: ")
    while True:
        password = getpass.getpass()
        if getpass.getpass('Confirm: ') == password:
            break
    with rent.model.session() as s:
        rent.model.create_user(s, username, password)
    print "Done!"

if __name__ == '__main__':
    main()
