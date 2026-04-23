import sys
from web3 import Web3

if len(sys.argv) < 6:
   print(f"Usage: python {sys.argv[0]} <rpc_url> <private_key> <from_addr> <to_addr> <amount_eth> [<chain_id>]")
   sys.exit(1)

rpc_url     = sys.argv[1]
private_key = sys.argv[2]
from_addr   = sys.argv[3]
to_addr     = sys.argv[4]
amount_eth  = float(sys.argv[5])
chain_id    = int(sys.argv[6]) if len(sys.argv) > 6 else 1337  # Default chain_id is 1337

w3 = Web3(Web3.HTTPProvider(rpc_url))

# Convert addresses to checksum format for Web3.py safety requirements
from_addr = w3.to_checksum_address(from_addr)
to_addr = w3.to_checksum_address(to_addr)

# Nonce for sending account
nonce = w3.eth.get_transaction_count(from_addr)
gas_price = w3.eth.gas_price

print(f"Current nonce for {from_addr}: {nonce}")
print(f"Gas price: {gas_price}")

tx = {
   "nonce": nonce,
   "to": to_addr,
   "value": w3.to_wei(amount_eth, "ether"),
   "gas": 21000,
   "gasPrice": gas_price,
   "chainId": chain_id,
}

signed_tx = w3.eth.account.sign_transaction(tx, private_key)
raw_tx = signed_tx.raw_transaction.hex()

print("Raw transaction hex:\n", raw_tx)
print("Sending transaction...")

try:
   tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
   print("Transaction hash:", tx_hash.hex())
except Exception as e:
   if "Known transaction" in str(e):
       print("Warning: Transaction already exists in mempool/blockchain")
       print("This might mean:")
       print("1. Transaction was already sent successfully")
       print("2. Transaction is still pending")
       print("Check your balance or transaction status on the blockchain")
   else:
       print(f"Error sending transaction: {e}")
       sys.exit(1)
