from flask import Flask, request

from Pyfhel import Pyfhel, PyPtxt, PyCtxt

from util import handle_errors
from db import Database, Person

app = Flask(__name__)

@app.route('/')
@handle_errors()
def index():
    return {'endpoints': [
        'GET /names',
        'POST /people (name, pubkey)',
        'DELETE /people/<name>',
        'GET /balance/<name>',
        'GET /pubkey/<name>',
        'GET /privkey/<name>',
        'POST /transfer (src, dst, amount_src_ciphertext, amount_dst_ciphertext)',
        'GET /save_db'
    ]}

@app.route('/names', methods=['GET'])
def get_names():
    db = Database.instance()

    people = db.get_people()
    return {'names': [person.name for person in people]}

@app.route('/people', methods=['POST'])
def add_person():
    print(request)
    print(request.json)

    db = Database.instance()

    db.add_person(request.get_json().get('name'), bytes.fromhex(request.get_json().get('pubkey')))
    save_db()
    return {}, 200

@app.route('/people/<name>', methods=['DELETE'])
def remove_person(name):
    db = Database.instance()

    db.remove_person(name)
    save_db()

    return {}, 200

@app.route('/balance/<name>', methods=['GET'])
def get_balance(name):
    db = Database.instance()

    balance = db.get_balance(name)
    return balance.hex()

@app.route('/pubkey/<name>', methods=['GET'])
def get_pubkey(name):
    db = Database.instance()

    pubkey: bytes = db.get_pubkey(name)
    return pubkey.hex()

@app.route('/privkey/<name>', methods=['GET'])
def get_privkey(name):
    db = Database.instance()

    privkey: bytes = db.get_privkey(name)
    return privkey.hex()

@app.route('/transfer', methods=['POST'])
def transfer():
    src = request.get_json().get('src')
    dst = request.get_json().get('dst')
    amount_src_ciphertext = request.get_json().get('amount_src_ciphertext')
    amount_dst_ciphertext = request.get_json().get('amount_dst_ciphertext')

    db = Database.instance()

    db.transfer(src, dst, bytes.fromhex(amount_src_ciphertext), bytes.fromhex(amount_dst_ciphertext))
    
    save_db()
    return {}, 200

@app.route('/save_db')
def save_db():
    Database.write_to_file('mock.txt')

    return {}, 200
