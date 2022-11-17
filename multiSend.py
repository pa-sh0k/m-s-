from web3 import Web3
from config import *

myAddress = MAIN_ADDRESS
privatekey = PRIVATE_KEY

w3 = Web3(Web3.HTTPProvider("https://eth-goerli.public.blastapi.io"))

MultiSender = w3.eth.contract(
    address="0xe05A3e1221C74737754A51859f79378eb8fCc2f4",
    abi=open("ABIs/MultiABI.json").read(),
)

# addresses - массив адресов, на которые вы раскидываете, amount -  число в wei, которое вы раскидываете на каждый из кошелей
def multisend(addresses: list, amount: int) -> None:
    amount = int(amount * 10**18)
    toSend = len(addresses) * amount
    txFeatures = {
        "chainId": 5,
        "gas": 2500000,
        "gasPrice": GWEI * 1000000000,
        "from": myAddress,
        "nonce": w3.eth.getTransactionCount(myAddress),
        "value": toSend,
    }
    tx = MultiSender.functions.multiSend(
        addresses, amount, int(len(addresses))
    ).buildTransaction(txFeatures)
    signedTxn = w3.eth.account.sign_transaction(tx, private_key=privatekey)
    buyTx = w3.eth.send_raw_transaction(signedTxn.rawTransaction)
    w3.eth.wait_for_transaction_receipt(buyTx.hex())
    print(f"https://goerli.etherscan.io/tx/{buyTx.hex()}")


if __name__ == "__main__":
    with open("accounts.csv", "r") as f:
        lines = f.readlines()
        accounts = list(map(lambda x: list(x.split(","))[0], lines))
    for i in range(1, len(accounts) // 40):
        multisend(accounts[(i - 1) * 40 : i * 40], ETH_AMOUNT_PER_WALLET)
    if len(accounts) % 40 != 0:
        multisend(accounts[len(accounts) - len(accounts) % 40 :], ETH_AMOUNT_PER_WALLET)
