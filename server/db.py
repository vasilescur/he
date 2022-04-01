"""
Mock database implementation for storing and retrieving data.
"""

from typing import List

from Pyfhel import Pyfhel, PyPtxt, PyCtxt

class Person:
    def __init__(self, name):
        self.name = name
        self.balance_ciphertext = None
        self.transactions = []
        self.HE = None

    def serialize(self) -> str:
        return f'{self.name}|{self.balance_ciphertext}\n' + '\n'.join([t.serialize() for t in self.transactions])
    
    @staticmethod
    def deserialize(string: str):
        lines = string.split('\n')
        name, balance_ciphertext = lines[0].split('|')
        transactions = [Transaction.deserialize(line) for line in lines[1:-1]]

        person = Person(name)
        person.balance_ciphertext = balance_ciphertext
        person.transactions = transactions

        return person


class Transaction:
    def __init__(self, src, dst, amount):
        self.sender = src
        self.receiver = dst
        self.amount = amount

    def serialize(self) -> str:
        return f"{self.sender}|{self.receiver}|{self.amount}"
    
    @staticmethod
    def deserialize(string: str):
        parts = string.strip().split('|')
        return Transaction(parts[0], parts[1], parts[2])


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
                Database._instance.HE.contextGen(p=65537)
                Database._instance.HE.keyGen()
                Database._instance.people = {}
                Database._instance.add_mock_people()
            
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
            self.add_person(name)

    def get_people(self) -> List[Person]:
        return list(self.people.values())

    def get_balance(self, name) -> Person:
        person = self.people[name]
        return person.balance_ciphertext
    
    def get_transactions(self, name) -> Person:
        person = self.people[name]
        return person.transactions

    def add_person(self, name) -> None:
        if name in self.people:
            raise Exception(f'{name} already exists')
        
        self.people[name] = Person(name)
        self.people[name].HE = Pyfhel()
        self.people[name].HE.contextGen(p=65537)
        self.people[name].HE.keyGen()

    def remove_person(self, name) -> None:
        del self.people[name]

    def get_pubkey(self, name) -> bytes:
        return self.people[name].HE.to_bytes_publicKey()

    def get_privkey(self, name) -> bytes:
        return self.people[name].HE.to_bytes_secretKey()

    def transfer(self, src_name: str, dst_name: str, amount_src_ciphertext, amount_dst_ciphertext) -> None:
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

        # Reduce the balance of the sender
        src_HE = self.get_HE(src_name)
        src_start_balance = src.balance_ciphertext
        src_end_balance = src.HE.sub(src_start_balance, amount_src_ciphertext)
        src.balance_ciphertext = src_end_balance

        # Increase the balance of the receiver
        dst_HE = self.get_HE(dst_name)
        dst_start_balance = dst.balance_ciphertext
        dst_end_balance = dst.HE.add(dst_start_balance, amount_dst_ciphertext)
        dst.balance_ciphertext = dst_end_balance

        # Add a transaction to the sender
        src.transactions.append(Transaction(src_name, dst_name, amount_src_ciphertext))

        # Add a transaction to the receiver
        dst.transactions.append(Transaction(dst_name, src_name, amount_dst_ciphertext))
