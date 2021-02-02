#!/usr/bin/python3

import pytest
import brownie
from brownie import CurveTokenV1, CurveTokenV2
from brownie.test import given, strategy
from hypothesis import settings

# Was Reward Token 1 instantiated to Bob?
def test_reward_added(multi_reward, accounts, reward_token, bob):
    assert multi_reward.rewardData(reward_token)[0] == bob


# Was Reward Token 1 instantiated to Charlie?
def test_reward2_added(multi_reward, accounts, reward_token2, charlie):
    assert multi_reward.rewardData(reward_token2)[0] == charlie


# Owner cannot modify reward
def test_owner_cannot_modify_reward(multi_reward, accounts, reward_token, alice):
    with brownie.reverts():
        multi_reward.addReward(reward_token, alice, 3600, {"from": alice})


# Distributor cannot modify reward
def test_distributor_cannot_modify_reward(
    multi_reward, accounts, reward_token, alice, bob
):
    with brownie.reverts():
        multi_reward.addReward(reward_token, alice, 3600, {"from": bob})


# No user can modify reward
@pytest.mark.parametrize("account_id", range(5))
@pytest.mark.parametrize("account_id2", range(5))
def test_reward_unmodifiable(
    multi_reward, accounts, reward_token, account_id, account_id2
):
    with brownie.reverts():
        multi_reward.addReward(
            reward_token, accounts[account_id], 3600, {"from": accounts[account_id2]}
        )


# Can distributor set reward?
def test_set_rewards_distributor(multi_reward, accounts, reward_token, alice, bob):
    multi_reward.setRewardsDistributor(reward_token, bob, {"from": alice})
    assert multi_reward.rewardData(reward_token)[0] == bob


# The owner of the reward token can mint for new accounts
@pytest.mark.parametrize("account_id", range(5))
def test_owner_can_mint(multi_reward, accounts, reward_token, alice, account_id):
    reward_token.mint(accounts[account_id], 10 ** 10, {"from": alice})
    assert reward_token.balanceOf(alice) >= 10 ** 10


# The distributor cannot mint reward tokens
@pytest.mark.parametrize("account_id", range(1, 5))
def test_distributor_cannot_mint(multi_reward, accounts, reward_token, account_id):
    _account = accounts[account_id]
    with brownie.reverts():
        reward_token.mint(_account, 10 ** 19, {"from": _account})


# Are owners able to update reward notification?
def test_owner_notify_reward_amount(
    multi_reward, accounts, reward_token, alice, bob, base_token, chain
):
    reward_token.approve(multi_reward, 10 ** 19)
    multi_reward.setRewardsDistributor(reward_token, alice, {"from": alice})
    multi_reward.notifyRewardAmount(reward_token, 10 ** 10, {"from": alice})
    assert multi_reward.getRewardForDuration(reward_token) > 0


# Random users should not be able to access notifyRewardAmount
def test_rando_notify_reward_amount(
    multi_reward, accounts, reward_token, alice, bob, charlie, base_token, chain
):
    reward_token.approve(multi_reward, 10 ** 19)
    reward_token.approve(charlie, 10 ** 19)
    multi_reward.setRewardsDistributor(reward_token, bob, {"from": alice})
    with brownie.reverts():
        multi_reward.notifyRewardAmount(reward_token, 10 ** 10, {"from": charlie})
