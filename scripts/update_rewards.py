from brownie import Contract, MultiRewards, accounts
from brownie.network.gas.strategies import GasNowScalingStrategy

# address of the StakingRewards contract
MULTIREWARDS_CONTRACT_ADDRESS = "0x"
REWARDTOKEN_CONTRACT_ADDRESS = "0x"

# address that owns `StakingRewards`
OWNER = accounts.add()
# address that is permitted to fund the contract
REWARD_ADMIN = accounts.add()

# amount to add as a reward
REWARDS_AMOUNT = 10 ** 19


gas_strategy = GasNowScalingStrategy("standard", "fast")


def main():
    multi = MultiRewards.at(MULTIREWARDS_CONTRACT_ADDRESS)
    reward = Contract(REWARDTOKEN_CONTRACT_ADDRESS)

    # sanity check on the reward amount
    if REWARDS_AMOUNT < 10 ** reward.decimals():
        raise ValueError("Reward amount is less than 1 token - are you sure this is correct?")

    # ensure the reward admin has sufficient balance of the reward token
    if reward.balanceOf(REWARD_ADMIN) < REWARDS_AMOUNT:
        raise ValueError("Rewards admin has insufficient balance to fund the contract")

    # ensure the reward contract has sufficient allowance to transfer the reward token
    if reward.allowance(REWARD_ADMIN, multi) < REWARDS_AMOUNT:
        reward.approve(multi, 2 ** 256 - 1, {"from": REWARD_ADMIN, "gas_price": gas_strategy})

    # update the reward amount
    multi.notifyRewardAmount(
        reward, REWARDS_AMOUNT, {"from": REWARD_ADMIN, "gas_price": gas_strategy}
    )

    print(f"Success! {REWARDS_AMOUNT/10**reward.decimals():.2f} {reward.symbol()} has been added")
