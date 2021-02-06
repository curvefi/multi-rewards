#!/usr/bin/python3

import brownie
from brownie.test import given, strategy



# Make sure a user who has not staked cannot withdraw
@given(amount=strategy("uint256", max_value=10 ** 25))
def test_unstaked_cannot_withdraw(multi, bob, amount):
    with brownie.reverts():
        multi.withdraw(amount, {"from": bob})


# Does the amount received match up with earn?
@given(time=strategy("uint256", max_value=31557600, min_value=60))
def test_amount_received(multi, reward_token, alice, chain, time):
    reward_token.approve(multi, 10 ** 19, {"from": alice})

    multi.stake(10 ** 10, {"from": alice})
    multi.setRewardsDistributor(reward_token, alice, {"from": alice})
    multi.notifyRewardAmount(reward_token, 10 ** 10, {"from": alice})
    reward_token.balanceOf(alice)

    chain.mine(timedelta=time)
    earned = multi.earned(alice, reward_token)
    reward_duration = multi.getRewardForDuration(reward_token)
    assert reward_duration == earned


# Does the exit function successfully withdraw?
@given(amount=strategy("uint256", min_value=(10 ** 2), max_value=(10 ** 16)))
def test_exit(multi, reward_token, alice, amount):
    reward_token.approve(multi, 10 ** 19, {"from": alice})
    multi.setRewardsDistributor(reward_token, alice, {"from": alice})
    multi.stake(amount, {"from": alice})
    assert multi.balanceOf(alice) == amount

    multi.exit({"from": alice})
    assert multi.balanceOf(alice) == 0
