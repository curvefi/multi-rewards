#!/usr/bin/python3

import brownie
from brownie.test import given, strategy


# Can the owner stake and then withdraw?
@given(amount=strategy("uint256", max_value=10 ** 18, exclude=0))
# @settings(max_examples=5)
def test_owner_withdraw(multi, accounts, alice, amount):
    multi.stake(amount, {"from": alice})
    multi.withdraw(amount, {"from": alice})
    assert multi.balanceOf(alice) == 0


# Make sure a user who has not staked cannot withdraw
@given(amount=strategy("uint256", max_value=10 ** 25))
def test_unstaked_cannot_withdraw(multi, accounts, bob, amount):
    with brownie.reverts():
        multi.withdraw(amount, {"from": bob})


# User should not be able to withdraw a reward if empty
def test_cannot_get_empty_reward(multi, reward_token, accounts, alice):
    # XXX Add some cycles
    # _amount=multi.getRewardForDuration(reward_token, {"from": alice})
    _init_amount = reward_token.balanceOf(alice)
    multi.getReward({"from": alice})
    _final_amount = reward_token.balanceOf(alice)
    assert _init_amount == _final_amount


# Can user retrieve reward after a time cycle?
def test_get_reward(multi, reward_token, accounts, alice, chain, issue):
    multi.getReward({"from": alice})
    _final_amount = reward_token.balanceOf(alice)
    assert _final_amount > issue


# Does the exit function successfully withdraw?
def test_exit(multi, reward_token, accounts, alice, chain, issue):
    multi.exit({"from": alice})
    _final_amount = reward_token.balanceOf(alice)
    assert _final_amount > issue


# Does the ERC20 recovery function produce expected behavior?
def test_recovery(multi, reward_token, accounts, alice, chain, issue):
    multi.recoverERC20(reward_token, 10 ** 10, {"from": alice})
    _final_amount = reward_token.balanceOf(alice)
    assert _final_amount > issue


# ERC20 function should fail on non-owner
def test_recovery_onlyowner(multi, reward_token, alice, bob, chain, issue):
    with brownie.reverts():
        multi.recoverERC20(reward_token, 10 ** 10, {"from": bob})
