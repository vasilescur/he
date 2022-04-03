from typing import Dict, List

import requests

from Pyfhel import Pyfhel, PyPtxt, PyCtxt
P = 65537

ENDPOINT = 'http://127.0.0.1:5000'


pubkeys: Dict[str, bytes] = {}

me = None


def encrypt(value: float, pubkey: bytes) -> bytes:
    HE = Pyfhel()
    HE.contextGen(p=P)
    HE.from_bytes_publicKey(pubkey)

    cipher = HE.encryptInt(int(value * 100))
    return cipher.to_bytes()


def set_ident(name: str):
    global me
    me = {'name': name}


def get_names() -> List[str]:
    req = requests.get(ENDPOINT + '/names').json()
    return req['names']

def get_pubkey(name: str) -> str:
    if name in pubkeys:
        return pubkeys[name]

    pubkey = requests.get(ENDPOINT + '/pubkey/' + name).text
    pubkeys[name] = bytes.fromhex(pubkey)
    return pubkeys[name]

def fetch_keys():
    for name in get_names():
        get_pubkey(name)


def get_balance() -> float:
    req = requests.get(ENDPOINT + f'/balance/{me["name"]}')
    cipher: bytes = bytes.fromhex(req.text.strip())
    ciphertext: PyCtxt = PyCtxt(pyfhel=me['HE'], serialized=cipher, encoding='int')
    balance: float = me['HE'].decryptInt(ciphertext) / 100
    return balance


def create_user(name: str, pubkey: bytes):
    req = requests.post(ENDPOINT + '/people', json={
        'name': name,
        'pubkey': pubkey.hex(),
    })
    return req.status_code

def save_db():
    requests.get(ENDPOINT + '/save_db')


def main():
    global me 

    while True:
        try:
            print('> ', end='')
            cmd = input().strip()
            
            if cmd.startswith('Log in '):
                name = cmd.split(' ')[2]

                set_ident(name)

                # Initialize my HE 
                me['HE'] = Pyfhel()
                me['HE'].contextGen(p=P)
                me['HE'].restorepublicKey(f'{name}.pub')
                me['HE'].restoresecretKey(f'{name}')

                fetch_keys()

                print(f'Welcome, {name}. Fetched {len(pubkeys)} public keys.')

            elif cmd.startswith('Create user '):
                name = cmd.split(' ')[2]
                set_ident(name)

                # Generate keypair
                me['HE'] = Pyfhel()
                me['HE'].contextGen(p=P)
                me['HE'].keyGen()

                # Save keypair
                me['HE'].savepublicKey(f'{name}.pub')
                me['HE'].savesecretKey(f'{name}')

                # Inform the server
                status = create_user(name, me['HE'].to_bytes_publicKey())
                
                if status == 200:
                    print(f'Created user {name}')
                else:
                    print(f'Failed to create user {name}')

            elif cmd == 'names':
                print(get_names())

            elif cmd == 'fetch keys':
                fetch_keys()

            elif cmd.startswith('pubkey'):
                if len(cmd.split()) == 2:
                    print(get_pubkey(cmd.split()[1]).hex())
                else:
                    if me is None:
                        print('Error: not logged in.')
                        continue
                    
                    print(get_pubkey(me['name']).hex())

            elif cmd == 'balance':
                balance: float = get_balance()
                print(f'$ {balance}')

            elif cmd == 'quit':
                break

            elif cmd == 'save db':
                save_db()

            else:
                print('Unknown command')

        except KeyboardInterrupt:
            exit(0)

        print()

if __name__ == '__main__':
    main()
