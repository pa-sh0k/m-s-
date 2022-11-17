from config import ACCOUNT_AMOUNT
import random
import string
import threading
import secrets
from web3.auto import w3
from eth_account import Account

DEFAULT_PASSWORD_LENGTH = 15
DEFAULT_FILENAME = "accounts.csv"
FILE_LOCK = threading.Lock()


class Mail:
    def __init__(self):
        self.account = {
            "mail": {
                "email": "",
                "password": "",
            },
            "web3": {"address": "", "privateKey": ""},
        }

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
        return self.account["web3"]

    def save(self, fileName=DEFAULT_FILENAME):
        FILE_LOCK.acquire()
        with open(fileName, "a") as f:
            f.write(
                f"{self.account['web3']['address']},"
                f"{self.account['web3']['privateKey']}\n"
            )
        FILE_LOCK.release()


def run():
    n = ACCOUNT_AMOUNT
    for i in range(n):
        mail = Mail()
        mail.generateAccount()
        mail.save()
    print(f"Generated {n} accounts to {DEFAULT_FILENAME}")


if __name__ == "__main__":
    run()
