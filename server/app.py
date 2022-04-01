from flask import Flask

from Pyfhel import Pyfhel, PyPtxt, PyCtxt

from db import Database, Person

app = Flask(__name__)

@app.route('/')
def hello_world():
    db = Database.instance()

    people = db.get_people()
    return str([person.name for person in people])

@app.route('/add_person/<name>')
def add_person(name):
    db = Database.instance()
    
    try:
        db.add_person(name)
    except:
        return f'Failed to add {name}'
    
    save_db()

    return f'Added {name}'

@app.route('/remove_person/<name>')
def remove_person(name):
    db = Database.instance()

    db.remove_person(name)
    save_db()

    return f'Removed {name}'

@app.route('/get_balance/<name>')
def get_balance(name):
    db = Database.instance()

    balance = db.get_balance(name)
    return str(balance)

@app.route('/get_pubkey/<name>')
def get_pubkey(name):
    db = Database.instance()

    pubkey: bytes = db.get_pubkey(name)
    return pubkey.hex()

@app.route('/get_privkey/<name>')
def get_privkey(name):
    db = Database.instance()

    privkey: bytes = db.get_privkey(name)
    return privkey.hex()

@app.route('/transfer/<src>/<dst>/<amount_src_ciphertext>/<amount_dst_ciphertext>')
def transfer(src, dst, amount_src_ciphertext, amount_dst_ciphertext):
    db = Database.instance()

    try:
        db.transfer(src, dst, bytes.fromhex(amount_src_ciphertext), bytes.fromhex(amount_dst_ciphertext))
    except:
        return f'Failed to transfer from {src} to {dst}'
    
    save_db()

    return f'Transferred from {src} to {dst}'

@app.route('/save_db')
def save_db():
    Database.write_to_file('mock.txt')
    return 'saved'


