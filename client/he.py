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

def get_pubkey(name: str) -> bytes:
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
        print()
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
                if me is None:
                    print('Error: not logged in.')
                    continue

                balance: float = get_balance()
                print(f'$ {balance}')

            elif cmd == 'transfer':
                if me is None:
                    print('Error: not logged in.')
                    continue

                print('Target: ', end='')
                dst = input().strip()

                if dst not in pubkeys or dst == me['name']:
                    print('Error: invalid target.')
                    continue

                print('Amount: ', end='')
                amount = float(input().strip())

                if amount < 0:
                    print('Error: amount must be positive.')
                    continue

                # --- Critical section ---
                # We assume (must find way to ensure) this is tamper-proof.

                balance: float = get_balance()
                if balance < amount:
                    print('Error: insufficient balance.')
                    continue

                src_cipher: bytes = encrypt(amount, get_pubkey(me['name']))
                dst_cipher: bytes = encrypt(amount, get_pubkey(dst))
                
                req = requests.post(ENDPOINT + '/transfer', json={
                    'src': me['name'],
                    'dst': dst,
                    'amount_src_ciphertext': src_cipher.hex(),
                    'amount_dst_ciphertext': dst_cipher.hex(),
                })

                # --- End critical section ---

                if req.status_code == 200:
                    print(f'Sent {amount} to {dst}.')
                else:
                    print(f'Failed to send {amount} to {dst}. Status code: {req.status_code}')

            elif cmd == 'transactions':
                if me is None:
                    print('Error: not logged in.')
                    continue

                req = requests.get(ENDPOINT + f'/transactions/{me["name"]}')
                
                if req.status_code != 200:
                    print('Error: failed to fetch transactions.')
                    continue

                transactions = req.json()['transactions']
                for t in transactions:
                    amt_cipher = PyCtxt(pyfhel=me['HE'], serialized=bytes.fromhex(t['amount']), encoding='int')
                    amt: float = me['HE'].decryptInt(amt_cipher) / 100

                    print(f'{t["src"]} -> {t["dst"]}: $ {amt:.2f}')

            elif cmd == 'quit' or cmd == 'exit':
                break

            elif cmd == 'save db':
                save_db()

            else:
                print('Unknown command. Available commands:')
                print('  names/Log in <name>/Create user <name>')
                print('  fetch keys/pubkey <name>')
                print('  balance/transfer')
                print('  quit/exit/save db')

        except KeyboardInterrupt:
            exit(0)


if __name__ == '__main__':
    main()
