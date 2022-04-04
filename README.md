# he
Money transfer app using homomorphic encryption

## Introduction

Homomorphic encryption allows simple arithmetic operations in ciphertext space.
This means that the users can submit encrypted values,
        the server operates on those encrypted values and returns an encrypted result,
        which the user can decrypt and read.
Essentially, it allows us to safely perform a specific server-side computation
        without having access to the actual values being computed.

## Design

In this demo app's client-server architecture,
        a server keeps track of the users and their (encrypted) balances, public keys, and transaction history.
Meanwhile, each user's client software keeps track of their private key.

When a user wants to submit a transaction,
        the client encrypts the transaction amount once with the sender's public key,
        and once with the recipient's public key,
        and sends these encrypted values to the server.
The server uses a homomorphic encryption library to process the transaction by 
        adding/subtracting the encrypted values to the sender/recipient's encrypted balances.

Users may query their own balance and transaction history at any time and decrypt it using their secret key.

