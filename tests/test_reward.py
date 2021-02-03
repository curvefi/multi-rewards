#!/usr/bin/python3

import brownie
import pytest
from brownie.test import given, strategy
from hypothesis import settings


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


# Reward per token accurate?
@given(_amt=strategy("uint256", max_value=(10 ** 17), exclude=0))
def test_reward_per_token(multi, alice, reward_token, issue, _amt, chain):
    multi.notifyRewardAmount(reward_token, _amt, {"from": alice})
    _init_rpt = multi.rewardPerToken(reward_token)

    chain.mine(timedelta=100)
    assert _init_rpt + _amt > multi.rewardPerToken(reward_token) * 0.98
    assert _init_rpt + _amt < multi.rewardPerToken(reward_token) * 1.02


# Rewards struct updates as expected
@given(_amt=strategy("uint256", min_value=(10 ** 10), max_value=(10 ** 16), exclude=0))
def test_rewards_update(multi, alice, reward_token, issue, _amt, chain, base_token):
    _r = []
    _r.append(multi.rewardData(reward_token))
    chain.mine(timedelta=60)
    for i in range(1, 5):
        multi.notifyRewardAmount(reward_token, _amt, {"from": alice})
        chain.mine(timedelta=60)

        _r.append(multi.rewardData(reward_token))
        assert _r[i - 1]["periodFinish"] < _r[i]["periodFinish"]
        assert _r[i - 1]["lastUpdateTime"] < _r[i]["lastUpdateTime"]
        assert _r[i - 1]["rewardPerTokenStored"] <= _r[i]["rewardPerTokenStored"]


# Is last reward time applicable correct?
@given(_amt=strategy("uint256", max_value=(10 ** 16), exclude=0))
def test_last_time_reward_applicable(multi, reward_token, chain, _amt, alice):
    _last_time = multi.lastTimeRewardApplicable(reward_token)
    for i in range(5):
        multi.notifyRewardAmount(reward_token, _amt, {"from": alice})
        chain.mine(timedelta=60)
        _curr_time = multi.lastTimeRewardApplicable(reward_token)
        assert _curr_time > _last_time
        _last_time = _curr_time


# Reward per duration accurate?
@given(_amt=strategy("uint256", max_value=(10 ** 17), exclude=0))
def test_reward_per_duration(multi, reward_token, _amt, alice):
    multi.notifyRewardAmount(reward_token, _amt, {"from": alice})
    multi.getRewardForDuration(reward_token) > _amt * 0.95
    multi.getRewardForDuration(reward_token) < _amt * 1.05


# Reward per token paid accurate?
def test_reward_per_token_paid(multi, reward_token, alice, chain):
    for i in range(5):
        _last_val = multi.userRewardPerTokenPaid(alice, reward_token)
        multi.notifyRewardAmount(reward_token, 10 ** 10, {"from": alice})
        chain.mine(timedelta=60)
        multi.getReward()
        assert multi.userRewardPerTokenPaid(alice, reward_token) > _last_val


# Will Alice, Bob and Charlie earn correct reward amounts?
@given(_am1=strategy("uint256", max_value=10 ** 19, exclude=0))
@given(_am2=strategy("uint256", max_value=10 ** 19, exclude=0))
@settings(max_examples=5)
def test_multiple_reward(
    multi,
    reward_token,
    reward_token2,
    alice,
    bob,
    charlie,
    accounts,
    chain,
    base_token,
    _am1,
    _am2,
):
    reward_token.approve(multi, 10 ** 19, {"from": bob})
    multi.setRewardsDistributor(reward_token, bob, {"from": alice})
    multi.notifyRewardAmount(reward_token, 10 ** 10, {"from": bob})

    reward_token2.approve(multi, 10 ** 19, {"from": charlie})
    multi.setRewardsDistributor(reward_token2, charlie, {"from": alice})
    multi.notifyRewardAmount(reward_token2, 10 ** 10, {"from": charlie})

    base_token.approve(multi, _am1, {"from": bob})
    multi.stake(_am1, {"from": bob})

    base_token.approve(multi, _am2, {"from": charlie})
    multi.stake(_am2, {"from": charlie})

    chain.mine(timedelta=60)

    for i in range(2):
        _e1 = (
            multi.balanceOf(accounts[i])
            * (
                multi.rewardPerToken(reward_token)
                - multi.userRewardPerTokenPaid(accounts[i], reward_token)
            )
        ) // (10 ** 18) + multi.rewards(accounts[i], reward_token)
        assert multi.earned(accounts[i], reward_token) == _e1

        _e2 = (
            multi.balanceOf(accounts[i])
            * (
                multi.rewardPerToken(reward_token2)
                - multi.userRewardPerTokenPaid(accounts[i], reward_token2)
            )
        ) // (10 ** 18) + multi.rewards(accounts[i], reward_token2)
        assert multi.earned(accounts[i], reward_token2) == _e2
