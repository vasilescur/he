# he
Money transfer app using homomorphic encryption

## The cool part

```python
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
```
