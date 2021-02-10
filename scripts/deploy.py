from brownie import MultiRewards, accounts
from brownie.network.gas.strategies import GasNowScalingStrategy

# the address that will be used to deploy the contract
# can be loaded via a keystore or private key, for more info see
# https://eth-brownie.readthedocs.io/en/stable/account-management.html
DEPLOYER = accounts.add()

# the address that owns the contract and can call all restricted functions
OWNER = DEPLOYER

# the address of the Curve LP token for your pool
STAKING_TOKEN_ADDRESS = "0x"

gas_strategy = GasNowScalingStrategy("standard", "fast")


def main():
    multi_rewards = MultiRewards.deploy(
        OWNER, STAKING_TOKEN_ADDRESS, {"from": DEPLOYER, "gas_price": gas_strategy}
    )

    print(
        f"""Success!
MultiRewards deployed to: {multi_rewards}
Owner: {OWNER}
Please verify the source code here: https://etherscan.io/verifyContract?a={multi_rewards}
Compiler version: 0.5.17
Optimization: ON
"""
    )
