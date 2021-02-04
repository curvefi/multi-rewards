#!/usr/bin/python3

import brownie
from brownie.test import given, strategy


# Can the owner stake and then withdraw?
@given(amount=strategy("uint256", max_value=10 ** 18, exclude=0))
def test_owner_withdraw(multi, alice, amount):
    multi.stake(amount, {"from": alice})
    multi.withdraw(amount, {"from": alice})
    assert multi.balanceOf(alice) == 0


# Make sure a user who has not staked cannot withdraw
@given(amount=strategy("uint256", max_value=10 ** 25))
def test_unstaked_cannot_withdraw(multi, bob, amount):
    with brownie.reverts():
        multi.withdraw(amount, {"from": bob})


# User should not be able to withdraw a reward if empty
@given(time=strategy("uint256", max_value=31557600))
def test_cannot_get_empty_reward(multi, reward_token, alice, chain, time):
    init_amount = reward_token.balanceOf(alice)
    chain.mine(timedelta=time)
    multi.getReward({"from": alice})
    final_amount = reward_token.balanceOf(alice)
    assert init_amount == final_amount


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
