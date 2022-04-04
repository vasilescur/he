"""
Mock database implementation for storing and retrieving data.
"""

from typing import List

from Pyfhel import Pyfhel, PyPtxt, PyCtxt
P = 65537


class Person:
    def __init__(self, name: str, pubkey: bytes):
        self.name = name
        self.transactions = []

        self.HE = Pyfhel()
        self.HE.contextGen(p=P)
        self.HE.from_bytes_publicKey(pubkey)

        balance = self.HE.encryptInt(20 * 100)    # start with $20
        self.balance_ciphertext: bytes = balance.to_bytes()

    def serialize(self) -> str:
        pubkey: bytes = self.HE.to_bytes_publicKey()
        return f'{self.name}|{pubkey.hex()}|{self.balance_ciphertext.hex()}\n' \
            + '\n'.join([t.serialize() for t in self.transactions])
    
    @staticmethod
    def deserialize(string: str):
        lines = string.split('\n')
        name, pubkey, balance_ciphertext = lines[0].split('|')
        transactions = [Transaction.deserialize(line) for line in lines[1:-1]]
        pubkey_bytes: bytes = bytes.fromhex(pubkey)

        person = Person(name, pubkey_bytes)
        person.balance_ciphertext = bytes.fromhex(balance_ciphertext)
        person.transactions = transactions

        return person


class Transaction:
    def __init__(self, src: str, dst: str, amount: bytes):
        self.src: str = src
        self.dst: str = dst
        self.amount: bytes = amount

    def serialize(self) -> str:
        return f"{self.src}|{self.dst}|{self.amount.hex()}"
    
    @staticmethod
    def deserialize(string: str):
        parts = string.strip().split('|')
        return Transaction(parts[0], parts[1], bytes.fromhex(parts[2]))


class Database:
    _instance = None

    def __init__(self) -> None:
        raise Exception('call instance() instead')

    @staticmethod
    def instance():
        if Database._instance is None:
            Database._instance = Database.__new__(Database)

            try:
                Database.read_from_file('mock.txt')
            except FileNotFoundError:
                Database._instance.HE = Pyfhel()
                Database._instance.HE.contextGen(p=P)
                Database._instance.HE.keyGen()
                Database._instance.people = {}
                # Database._instance.add_mock_people()
            
        return Database._instance

    @staticmethod
    def write_to_file(file_name: str) -> None:
        db = Database.instance()

        with open(file_name, 'w') as f:
            f.write('\n-\n'.join([person.serialize() for person in db.people.values()]))

        db.HE.saveContext('mock_context.bin')
        db.HE.savepublicKey('mock_pubkey.bin')
        db.HE.savesecretKey('mock_prvkey.bin')

        for person in db.people.values():
            person.HE.saveContext(f'pubkeys/{person.name}_context.bin')
            person.HE.savepublicKey(f'pubkeys/{person.name}.bin')

    @staticmethod
    def read_from_file(file_name: str) -> None:
        db = Database.instance()

        with open(file_name, 'r') as f:
            contents = f.read()
            people_strings = contents.split('\n-\n')
            people = [Person.deserialize(person_string) for person_string in people_strings]
            db.people = {person.name: person for person in people}

        db.HE = Pyfhel()
        db.HE.restoreContext('mock_context.bin')
        db.HE.restorepublicKey('mock_pubkey.bin')
        db.HE.restoresecretKey('mock_prvkey.bin')

        for person in db.people.values():
            person.HE = Pyfhel()
            person.HE.restoreContext(f'pubkeys/{person.name}_context.bin')
            person.HE.restorepublicKey(f'pubkeys/{person.name}.bin')

    def add_mock_people(self) -> None:
        for name in ['Alice', 'Bob', 'Charlie']:
            HE = Pyfhel()
            HE.contextGen(p=P)
            HE.keyGen()

            pubkey = HE.to_bytes_publicKey()
            self.add_person(name, pubkey)

    def get_people(self) -> List[Person]:
        return list(self.people.values())

    def get_balance(self, name) -> bytes:
        person = self.people[name]
        return person.balance_ciphertext
    
    def get_transactions(self, name) -> List[Transaction]:
        person = self.people[name]
        return person.transactions

    def add_person(self, name: str, pubkey: bytes) -> None:
        if name in self.people:
            raise Exception(f'{name} already exists')
        
        self.people[name] = Person(name, pubkey)

    def remove_person(self, name) -> None:
        del self.people[name]

    def get_pubkey(self, name) -> bytes:
        return self.people[name].HE.to_bytes_publicKey()

    def get_privkey(self, name) -> bytes:
        return self.people[name].HE.to_bytes_secretKey()

    def transfer(self, src_name: str, dst_name: str, amount_src: bytes, amount_dst: bytes) -> None:
        """
        Reduces the balance of the sender and increases the balance of the receiver, 
        without knowing either balance and without knowing the amount.

        NOTE: This function does not enforce any constraints on transactions, 
        such as blocking transactions from senders with insufficient funds. 
        This function does not (and cannot) ensure that the source and destination 
        balances are changed by the same amount, must trust client code to enforce.
        """
        
        src = self.people[src_name]
        dst = self.people[dst_name]

        amount_src_ciphertext: PyCtxt = PyCtxt(pyfhel=src.HE, serialized=amount_src, encoding='int')
        amount_dst_ciphertext: PyCtxt = PyCtxt(pyfhel=dst.HE, serialized=amount_dst, encoding='int')

        # Reduce the balance of the sender
        src_start_balance = PyCtxt(pyfhel=src.HE, serialized=src.balance_ciphertext, encoding='int')
        src_end_balance: PyCtxt = src.HE.sub(src_start_balance, amount_src_ciphertext)
        src.balance_ciphertext = src_end_balance.to_bytes()

        # Increase the balance of the receiver
        dst_start_balance = PyCtxt(pyfhel=dst.HE, serialized=dst.balance_ciphertext, encoding='int')
        dst_end_balance: PyCtxt = dst.HE.add(dst_start_balance, amount_dst_ciphertext)
        dst.balance_ciphertext = dst_end_balance.to_bytes()

        # Add a transaction to the sender
        src.transactions.append(Transaction(src_name, dst_name, amount_src))

        # Add a transaction to the receiver
        dst.transactions.append(Transaction(src_name, dst_name, amount_dst))

