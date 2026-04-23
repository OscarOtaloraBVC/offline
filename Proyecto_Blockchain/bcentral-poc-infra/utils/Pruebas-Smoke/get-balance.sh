echo "=== BALANCES ==="
echo

# Address 1 (FROM)
ADDR1="0x186dddc5375ca7b476ceb372253c9362cde6eb06" # Usada en las transacciones de testnet
BALANCE1=$(curl -s -X POST -H "Content-Type: application/json" -d "{\"jsonrpc\": \"2.0\", \"method\": \"eth_getBalance\", \"params\": [\"$ADDR1\", \"latest\"], \"id\": 1}" http://127.0.0.1:8545 | jq -r '.result')
BALANCE1_ETH=$(python3 -c "print(int('$BALANCE1', 16) / 10**18)")

echo "ADDRESS 2 (Sender):"
echo "  Address: $ADDR2"
echo "  Balance: $BALANCE2_ETH testETH"
echo

# Address 2 (FROM)
ADDR2="0x53a3fbebabd16b91be8da0116fef1f0dc80b8abd" # Usada en las transacciones de testnet
BALANCE2=$(curl -s -X POST -H "Content-Type: application/json" -d "{\"jsonrpc\": \"2.0\", \"method\": \"eth_getBalance\", \"params\": [\"$ADDR2\", \"latest\"], \"id\": 1}" http://127.0.0.1:8545 | jq -r '.result')
BALANCE2_ETH=$(python3 -c "print(int('$BALANCE2', 16) / 10**18)")

echo "ADDRESS 1 (Reciber):"
echo "  Address: $ADDR1"
echo "  Balance: $BALANCE1_ETH testETH"
echo


