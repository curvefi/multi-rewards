from brownie import Contract, MultiRewards, accounts
from brownie.network.gas.strategies import GasNowScalingStrategy

# address of the MultiRewards contract
MULTIREWARDS_CONTRACT_ADDRESS = "0x"
REWARDTOKEN_CONTRACT_ADDRESS = "0x"

# address that owns `Rewards`
OWNER = accounts.add()
# address that is permitted to fund the contract
REWARD_ADMIN = accounts.add()

# duration of the rewards period, in seconds - we recommend keeping this as 30 days
REWARDS_DURATION = 30 * 86400


gas_strategy = GasNowScalingStrategy("standard", "fast")


def main():
    multi = MultiRewards.at(MULTIREWARDS_CONTRACT_ADDRESS)
    reward = Contract(REWARDTOKEN_CONTRACT_ADDRESS)

    # Adding a new reward
    multi.addReward(reward, REWARD_ADMIN, REWARDS_DURATION, {"from": OWNER})

    print(f"Success! New reward token will be distributed over {REWARDS_DURATION/86400:.1f} days.")
