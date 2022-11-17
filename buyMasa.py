import logging
import random
import string
import threading
import secrets
from web3 import Web3
import cloudscraper
from faker import Faker
from web3.auto import w3
from eth_account import Account
from eth_account.messages import encode_defunct
import time
from config import GWEI

DEFAULT_MESSAGE = "I have read and accept the terms and conditions of the website."
DEFAULT_PASSWORD_LENGTH = 15
DEFAULT_FILENAME = "result.csv"
FILE_LOCK = threading.Lock()

FAKER = Faker()
FORMAT = (
    "%(asctime)s.%(msecs)03d\t%(levelname)s\t[%(filename)s:%(lineno)d]\t%(message)s"
)
logging.basicConfig(format=FORMAT, level=logging.INFO, datefmt="%H:%M:%S")
file_handler = logging.FileHandler("results.log")
file_handler.setFormatter(logging.Formatter(FORMAT))
logging = logging.getLogger(__name__)
logging.addHandler(file_handler)

WEB3 = Web3(Web3.HTTPProvider("https://eth-goerli.public.blastapi.io"))

SoulStore = w3.eth.contract(
    address="0x4454d3892124Ad4d859770660495461D1C5a37F3",
    abi=open("ABIs/SoulABI.json").read(),
)


class Mail:
    def __init__(self):
        self.account = {
            "mail": {
                "email": "",
                "password": "",
            },
            "web3": {"address": "", "privateKey": ""},
        }
        profile = FAKER.simple_profile()
        self.name = f"{profile['username']}.soul"
        self.session = cloudscraper.create_scraper()
        self.ar = "ar://"

    @staticmethod
    def filterText(text):
        bad_chars = [
            "/",
            "+",
            "-",
            '"',
            "'",
            "?",
            "!",
            "=",
            ",",
            ";",
            ":",
            "..",
            "(",
            ")",
            "[",
            "]",
        ]
        for char in bad_chars:
            text = text.replace(char, "")
        return text

    def generatePassword(self, length=DEFAULT_PASSWORD_LENGTH):
        self.account["mail"]["password"] = "".join(
            random.choices(string.digits + string.ascii_letters, k=length)
        )

    def generateAccount(self, passwordLength=DEFAULT_PASSWORD_LENGTH):
        private_key = "0x" + secrets.token_hex(32)
        account = Account.from_key(private_key)
        self.account["web3"] = dict(address=account.address, privateKey=private_key)
        self.generatePassword(passwordLength)

    def signMessage(self, message=DEFAULT_MESSAGE):
        message = encode_defunct(text=message)
        signed_message = w3.eth.account.sign_message(
            message, private_key=self.account["web3"]["privateKey"]
        )
        return signed_message.signature.hex()

    def save(self, fileName=DEFAULT_FILENAME):
        FILE_LOCK.acquire()
        with open(fileName, "a") as f:
            f.write(
                f"{self.account['web3']['address']},"
                f"{self.account['web3']['privateKey']},"
                f"{self.name}\n"
            )
        FILE_LOCK.release()

    def getChallenge(self):
        response = self.session.get(
            "https://beta.middleware.masa.finance/session/get-challenge"
        )
        return response.json()

    def checkSignature(self):
        message = "Welcome to 🌽Masa Finance!\n\nLogin with your soulbound web3 identity to unleash the power of DeFi.\n\nYour signature is valid till: {}.\nChallenge: {}"
        challenge = self.getChallenge()
        response = self.session.post(
            "https://beta.middleware.masa.finance/session/check-signature",
            json={
                "address": self.account["web3"]["address"],
                "signature": self.signMessage(
                    message.format(challenge["expires"], challenge["challenge"])
                ),
            },
        )
        return True

    def generate(self):
        response = self.session.post(
            "https://beta.middleware.masa.finance/storage/store",
            json={"soulName": self.name},
        ).json()
        self.ar = f'ar://{response["metadataTransaction"]["id"]}'
        return self.ar

    def mint(self):
        txFeatures = {
            "chainId": 5,
            "gas": 650000,
            "gasPrice": GWEI * 1000000000,
            "from": self.account["web3"]["address"],
            "nonce": WEB3.eth.getTransactionCount(self.account["web3"]["address"]),
            "value": 164922,
        }
        paymentMethod = "0x0000000000000000000000000000000000000000"
        yearsPeriod = 1
        tokenURI = self.ar
        tx = SoulStore.functions.purchaseIdentityAndName(
            paymentMethod, self.name, yearsPeriod, tokenURI
        ).buildTransaction(txFeatures)
        signedTxn = WEB3.eth.account.sign_transaction(
            tx, private_key=self.account["web3"]["privateKey"]
        )
        buyTx = WEB3.eth.send_raw_transaction(signedTxn.rawTransaction)
        return f"https://goerli.etherscan.io/tx/{buyTx.hex()}"

    def create(self):
        logging.info(self.checkSignature())
        logging.info(self.generate())
        logging.info(
            f"{self.account['web3']['address']}    |   {self.ar}   |   {self.name}"
        )
        logging.info(self.mint())

    def load(self, data):
        if str(type(data)) == "<class 'str'>":
            data = data.split(",")
            data = {
                "address": data[0],
                "privateKey": data[1],
            }
        self.account = {
            "web3": {
                "address": data["address"],
                "privateKey": data["privateKey"],
            },
            "mail": {
                "email": "",
                "password": "",
            },
        }


def run(mail):
    # mail.generateAccount()
    mail.create()
    mail.save()


def main():
    MAILS = []
    with open("accounts.csv", "r") as f:
        DATA = f.read().split("\n")[:-1]
    for wallet in DATA:
        mail = Mail()
        mail.load(wallet)
        MAILS.append(mail)
    threads = []
    for _ in range(len(DATA)):
        threads.append(threading.Thread(target=run, args=(MAILS[_],)))
        threads[-1].start()
        time.sleep(5)
    for thread in threads:
        thread.join()


if __name__ == "__main__":
    main()
