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
@given(t=strategy("uint256", max_value=31557600))
def test_cannot_get_empty_reward(multi, reward_token, alice, chain, t):
    _init_amount = reward_token.balanceOf(alice)
    chain.mine(timedelta=t)
    multi.getReward({"from": alice})
    _final_amount = reward_token.balanceOf(alice)
    assert _init_amount == _final_amount


# Can user retrieve reward after a time cycle?
@given(t=strategy("uint256", max_value=31557600))
def test_get_reward(multi, reward_token, alice, issue, chain, t):
    chain.mine(timedelta=t)
    multi.getReward({"from": alice})
    _final_amount = reward_token.balanceOf(alice)
    assert _final_amount > issue


# Does the amount received match up with earn?
@given(t=strategy("uint256", max_value=31557600))
def test_amount_received(multi, reward_token, alice, issue, chain, t):
    chain.mine(timedelta=t)
    _earned = multi.earned(alice, reward_token)
    _reward_duration = multi.getRewardForDuration(reward_token)
    assert _reward_duration == _earned


# Does the exit function successfully withdraw?
def test_exit(multi, reward_token, alice, issue):
    multi.exit({"from": alice})
    _final_amount = reward_token.balanceOf(alice)
    assert _final_amount > issue


# Does the ERC20 recovery function produce expected behavior?
def test_recovery(multi, reward_token, alice, issue):
    multi.recoverERC20(reward_token, 10 ** 10, {"from": alice})
    _final_amount = reward_token.balanceOf(alice)
    assert _final_amount > issue


# ERC20 function should fail on non-owner
def test_recovery_onlyowner(multi, reward_token, alice, bob, chain, issue):
    with brownie.reverts():
        multi.recoverERC20(reward_token, 10 ** 10, {"from": bob})
