#!/usr/bin/python3

import brownie
import pytest
from brownie.test import given, strategy
from hypothesis import settings


# No user can modify reward
@pytest.mark.parametrize("_id", range(5))
@pytest.mark.parametrize("_id2", range(5))
def test_reward_unmodifiable(multi, accounts, reward_token, _id, _id2):
    with brownie.reverts():
        multi.addReward(reward_token, accounts[_id], 3600, {"from": accounts[_id2]})


# Does last reward time update?
@given(_amt=strategy("uint256", max_value=(10 ** 16), exclude=0))
def test_last_time_reward_applicable(multi, reward_token, chain, _amt, alice):
    _last_time = multi.lastTimeRewardApplicable(reward_token)
    for i in range(5):
        multi.notifyRewardAmount(reward_token, _amt, {"from": alice})
        chain.mine(timedelta=60)
        _curr_time = multi.lastTimeRewardApplicable(reward_token)
        assert _curr_time > _last_time
        _last_time = _curr_time


# Reward per duration accurate?  Should round off and return full amount
@given(amount=strategy("uint256", max_value=(10 ** 17), exclude=0))
def test_reward_per_duration(multi, reward_token, amount, alice):
    reward_token.approve(multi, amount, {"from": alice})
    multi.setRewardsDistributor(reward_token, alice, {"from": alice})
    multi.notifyRewardAmount(reward_token, amount, {"from": alice})
    multi.getRewardForDuration(reward_token) == amount // 60 * 60


# Multiple tests for calculating correct multicoin reward amounts
@given(amount1=strategy("uint256", max_value=10 ** 19, exclude=0))
@given(amount2=strategy("uint256", max_value=10 ** 19, exclude=0))
@settings(max_examples=10)
def test_multiple_reward_earnings_act(
    multi,
    reward_token,
    reward_token2,
    alice,
    bob,
    charlie,
    accounts,
    chain,
    base_token,
    amount1,
    amount2,
):
    reward_amount = 10 ** 10
    reward_token.approve(multi, 10 ** 19, {"from": bob})
    multi.setRewardsDistributor(reward_token, bob, {"from": alice})
    multi.notifyRewardAmount(reward_token, 10 ** 10, {"from": bob})

    reward_token2.approve(multi, 10 ** 19, {"from": charlie})
    multi.setRewardsDistributor(reward_token2, charlie, {"from": alice})
    multi.notifyRewardAmount(reward_token2, 10 ** 10, {"from": charlie})

    base_token.approve(multi, amount1, {"from": bob})
    multi.stake(amount1, {"from": bob})

    base_token.approve(multi, amount2, {"from": charlie})
    multi.stake(amount2, {"from": charlie})

    # Check supply calculation is accurate
    assert multi.totalSupply() == amount1 + amount2
    chain.mine(timedelta=60)

    # Check reward per token calculation is accurate
    reward_per_token_stored = multi.rewardData(reward_token)["rewardPerTokenStored"]
    reward_rate = reward_amount // 60
    time_max = multi.lastTimeRewardApplicable(reward_token)
    time_min = multi.rewardData(reward_token)["lastUpdateTime"]
    interval = time_max - time_min
    rpt_calc = (interval * 10 ** 18 * reward_rate) // (amount1 + amount2)
    rpt = multi.rewardPerToken(reward_token)
    assert reward_per_token_stored + rpt_calc == rpt

    # Check earning calculation is accurate
    calc_earnings = (amount1 * rpt) // (10 ** 18)
    act_earnings = multi.earned(bob, reward_token)
    assert calc_earnings == act_earnings

    # Account for the amount already stored
    prepaid = multi.userRewardPerTokenPaid(charlie, reward_token)

    calc_earnings2 = (amount2 * (rpt - prepaid)) // (10 ** 18)
    act_earnings2 = multi.earned(charlie, reward_token)
    assert calc_earnings2 == act_earnings2


# Can user retrieve reward after a time cycle?
@given(time=strategy("uint256", max_value=31557600, min_value=60))
def test_get_reward(multi, reward_token, alice, issue, chain, time):
    chain.mine(timedelta=time)
    multi.getReward({"from": alice})
    final_amount = reward_token.balanceOf(alice)
    assert final_amount >= issue


# Reward per token accurate?
@given(amount=strategy("uint256", max_value=(10 ** 18), exclude=0))
def test_reward_per_token(multi, alice, bob, reward_token, amount, chain, base_token):
    reward_token.approve(multi, 10 ** 19, {"from": alice})
    multi.setRewardsDistributor(reward_token, alice, {"from": alice})
    multi.notifyRewardAmount(reward_token, 10 ** 10, {"from": alice})

    init_rpt = multi.rewardPerToken(reward_token)
    assert init_rpt == 0

    base_token.approve(multi, amount, {"from": bob})
    multi.stake(amount, {"from": bob})

    chain.mine(timedelta=100)
    final_rpt = multi.rewardPerToken(reward_token)

    assert final_rpt // (10 ** 18) == multi.earned(bob, reward_token) // amount


# Rewards struct updates as expected
@given(amount=strategy("uint256", min_value=(10 ** 10), max_value=(10 ** 16), exclude=0))
def test_rewards_update(multi, alice, reward_token, amount, chain, base_token):
    reward_token.approve(multi, amount, {"from": alice})
    multi.setRewardsDistributor(reward_token, alice, {"from": alice})
    multi.notifyRewardAmount(reward_token, amount, {"from": alice})
    multi.stake(amount, {"from": alice})

    rewards = []
    rewards.append(multi.rewardData(reward_token))
    chain.mine(timedelta=60)
    for i in range(1, 5):
        reward_token.approve(multi, amount, {"from": alice})
        multi.notifyRewardAmount(reward_token, amount, {"from": alice})
        multi.stake(amount, {"from": alice})
        chain.mine(timedelta=60)

        rewards.append(multi.rewardData(reward_token))
        curr = rewards[i]
        last = rewards[i - 1]

        assert last["periodFinish"] < curr["periodFinish"]
        assert last["lastUpdateTime"] < curr["lastUpdateTime"]
        assert last["rewardPerTokenStored"] < curr["rewardPerTokenStored"]
