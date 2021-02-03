#!/usr/bin/python3

import brownie
import pytest


# Was Reward Token 1 instantiated to Bob?
def test_reward_added(multi, accounts, reward_token, bob):
    assert multi.rewardData(reward_token)[0] == bob


# Was Reward Token 1 instantiated to Charlie?
def test_reward2_added(multi, accounts, reward_token2, charlie):
    assert multi.rewardData(reward_token2)[0] == charlie


# Owner cannot modify reward
def test_owner_cannot_modify_reward(multi, reward_token, alice):
    with brownie.reverts():
        multi.addReward(reward_token, alice, 3600, {"from": alice})


# No user can modify reward
@pytest.mark.parametrize("_id", range(5))
@pytest.mark.parametrize("_id2", range(5))
def test_reward_unmodifiable(multi, accounts, reward_token, _id, _id2):
    with brownie.reverts():
        _from = {"from": accounts[_id2]}
        multi.addReward(reward_token, accounts[_id], 3600, _from)


# Can distributor set reward?
def test_set_rewards_distributor(multi, reward_token, alice, bob):
    multi.setRewardsDistributor(reward_token, bob, {"from": alice})
    assert multi.rewardData(reward_token)[0] == bob


# The owner of the reward token can mint for new accounts
@pytest.mark.parametrize("account_id", range(5))
def test_owner_can_mint(accounts, reward_token, alice, account_id):
    _from = {"from": alice}
    reward_token._mint_for_testing(accounts[account_id], 10 ** 10, _from)
    assert reward_token.balanceOf(alice) >= 10 ** 10


# Are owners able to update reward notification?
def test_owner_notify_reward_amount(
    multi, accounts, reward_token, alice, bob, base_token, chain
):
    reward_token.approve(multi, 10 ** 19, {"from": alice})
    multi.setRewardsDistributor(reward_token, alice, {"from": alice})
    multi.notifyRewardAmount(reward_token, 10 ** 10, {"from": alice})
    assert multi.getRewardForDuration(reward_token) > 0


# Random users should not be able to access notifyRewardAmount
def test_rando_notify_reward_amount(multi, reward_token, alice, bob, charlie):
    multi.setRewardsDistributor(reward_token, bob, {"from": alice})
    with brownie.reverts():
        multi.notifyRewardAmount(reward_token, 10 ** 10, {"from": charlie})


# Cannot call notifyRewardAmount without Distributor set
def test_notify_without_distributor(multi, reward_token, alice):
    with brownie.reverts():
        multi.notifyRewardAmount(reward_token, 10 ** 10, {"from": alice})


# Will Alice, Bob, and Charlie all earn rewards?
def test_multiple_reward(
    multi, reward_token, reward_token2, alice, bob, charlie, chain, base_token
):
    reward_token.approve(multi, 10 ** 19, {"from": bob})
    multi.setRewardsDistributor(reward_token, bob, {"from": alice})
    multi.notifyRewardAmount(reward_token, 10 ** 10, {"from": bob})

    reward_token2.approve(multi, 10 ** 19, {"from": charlie})
    multi.setRewardsDistributor(reward_token2, charlie, {"from": alice})
    multi.notifyRewardAmount(reward_token2, 10 ** 10, {"from": charlie})

    base_token.approve(multi, 10 ** 5, {"from": bob})
    base_token.approve(multi, 10 ** 5, {"from": charlie})
    multi.stake(10 ** 5, {"from": bob})
    multi.stake(10 ** 5, {"from": charlie})

    chain.mine(timedelta=120)

    assert multi.earned(alice, reward_token) == 0
    assert multi.earned(bob, reward_token) > 0
    assert multi.earned(charlie, reward_token) > 0
    assert multi.earned(alice, reward_token2) == 0
    assert multi.earned(bob, reward_token2) > 0
    assert multi.earned(charlie, reward_token2) > 0
