from web3 import Web3


def withCustomError(customErrorString):
    errMsg = Web3.keccak(text=customErrorString)[:4].hex()
    return 'typed error: ' + errMsg

