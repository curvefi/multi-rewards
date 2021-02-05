#!/usr/bin/python3

import brownie
import pytest
from brownie.test import given, strategy
from hypothesis import settings


# No user can modify reward
@pytest.mark.parametrize("id1", range(5))
@pytest.mark.parametrize("id2", range(5))
def test_reward_unmodifiable(multi, accounts, reward_token, id1, id2):
    with brownie.reverts():
        multi.addReward(reward_token, accounts[id1], 3600, {"from": accounts[id2]})


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


@given(amount=strategy("uint256", min_value=0, max_value=1e77, exclude=0))
def test_multiplication_overflow(multi, reward_token, base_token, alice, chain, amount):
    base_token._mint_for_testing(alice, amount)
    base_token.approve(multi, amount, {"from": alice})
    multi.stake(amount, {"from": alice})

    reward_token._mint_for_testing(alice, amount)
    reward_token.approve(multi, amount, {"from": alice})
    multi.setRewardsDistributor(reward_token, alice, {"from": alice})
    multi.notifyRewardAmount(reward_token, amount, {"from": alice})

    chain.mine(timedelta=60)
    if amount < 1.157973e59:
        tot = multi.earned(alice, reward_token)
        assert tot >= (60 * multi.rewardData(reward_token)["rewardRate"]) * 0.99
        assert tot <= (60 * multi.rewardData(reward_token)["rewardRate"]) * 1.01
    else:
        with brownie.reverts("SafeMath: multiplication overflow"):
            tot = multi.earned(alice, reward_token)
