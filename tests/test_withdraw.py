#!/usr/bin/python3

import brownie
import pytest
from brownie import CurveTokenV1, CurveTokenV2
from brownie.test import given, strategy
from hypothesis import settings


# Can the owner stake and then withdraw?
@given(amount=strategy("uint256", max_value=10 ** 18, exclude=0))
# @settings(max_examples=5)
def test_owner_withdraw(multi_reward, accounts, alice, amount):
    multi_reward.stake(amount, {"from": alice})
    multi_reward.withdraw(amount, {"from": alice})
    assert multi_reward.balanceOf(alice) == 0


# Make sure a user who has not staked cannot withdraw
@given(amount=strategy("uint256", max_value=10 ** 25))
def test_unstaked_cannot_withdraw(multi_reward, accounts, bob, amount):
    with brownie.reverts():
        multi_reward.withdraw(amount, {"from": bob})


# User should not be able to withdraw a reward if empty
def test_cannot_get_empty_reward(multi_reward, reward_token, accounts, alice):
    # XXX Add some cycles
    _amount = multi_reward.getRewardForDuration(reward_token, {"from": alice})
    _init_amount = reward_token.balanceOf(alice)
    multi_reward.getReward({"from": alice})
    _final_amount = reward_token.balanceOf(alice)
    assert _init_amount == _final_amount


# Can user retrieve reward after a time cycle?
def test_get_reward(multi_reward, reward_token, accounts, alice, chain):
    multi_reward.stake(10 ** 18, {"from": alice})
    reward_token.approve(multi_reward, 10 ** 19)
    multi_reward.setRewardsDistributor(reward_token, alice, {"from": alice})
    multi_reward.notifyRewardAmount(reward_token, 10 ** 10, {"from": alice})
    _init_amount = reward_token.balanceOf(alice)
    chain.sleep(60)
    chain.mine()
    assert multi_reward.earned(alice, reward_token) > 0
    multi_reward.getReward({"from": alice})
    _final_amount = reward_token.balanceOf(alice)
    assert _final_amount > _init_amount


# Does the exit function successfully withdraw?
def test_exit(multi_reward, reward_token, accounts, alice, chain):
    multi_reward.stake(10 ** 18, {"from": alice})
    reward_token.approve(multi_reward, 10 ** 19)
    multi_reward.setRewardsDistributor(reward_token, alice, {"from": alice})
    multi_reward.notifyRewardAmount(reward_token, 10 ** 10, {"from": alice})
    _init_amount = reward_token.balanceOf(alice)
    chain.sleep(60)
    chain.mine()
    assert multi_reward.earned(alice, reward_token) > 0
    multi_reward.exit({"from": alice})
    _final_amount = reward_token.balanceOf(alice)
    assert _final_amount > _init_amount


# Does the ERC20 recovery function produce expected behavior?
def test_recover_erc20(multi_reward, reward_token, accounts, alice, chain):
    multi_reward.stake(10 ** 18, {"from": alice})
    reward_token.approve(multi_reward, 10 ** 19)
    multi_reward.setRewardsDistributor(reward_token, alice, {"from": alice})
    multi_reward.notifyRewardAmount(reward_token, 10 ** 10, {"from": alice})
    _init_amount = reward_token.balanceOf(alice)
    chain.sleep(60)
    chain.mine()
    assert multi_reward.earned(alice, reward_token) > 0
    multi_reward.recoverERC20(reward_token, 10 ** 10, {"from": alice})
    _final_amount = reward_token.balanceOf(alice)
    assert _final_amount > _init_amount


# ERC20 function should fail on non-owner
def test_recover_erc20_onlyowner(
    multi_reward, reward_token, accounts, alice, bob, chain
):
    multi_reward.stake(10 ** 18, {"from": alice})
    reward_token.approve(multi_reward, 10 ** 19)
    multi_reward.setRewardsDistributor(reward_token, alice, {"from": alice})
    multi_reward.notifyRewardAmount(reward_token, 10 ** 10, {"from": alice})
    _init_amount = reward_token.balanceOf(bob)
    chain.sleep(60)
    chain.mine()
    assert multi_reward.earned(alice, reward_token) > 0
    with brownie.reverts():
        multi_reward.recoverERC20(reward_token, 10 ** 10, {"from": bob})
    _final_amount = reward_token.balanceOf(bob)
    assert _final_amount == _init_amount
