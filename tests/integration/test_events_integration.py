#!/usr/bin/python3

from brownie.test import given, strategy


# Does the RewardAdded event fire?
@given(_amt=strategy("uint256", max_value=(10 ** 18), exclude=0))
def test_reward_added_fires(multi, reward_token, alice, _amt):
    multi.stake(10 ** 18, {"from": alice})
    reward_token.approve(multi, _amt, {"from": alice})
    multi.setRewardsDistributor(reward_token, alice, {"from": alice})
    tx = multi.notifyRewardAmount(reward_token, _amt, {"from": alice})

    assert tx.events["RewardAdded"].values() == [_amt]


# Does the Staked event fire?
@given(_amt=strategy("uint256", max_value=(10 ** 18), exclude=0))
def test_staked_fires(multi, alice, _amt):
    tx = multi.stake(_amt, {"from": alice})
    assert tx.events["Staked"].values()[0] == alice
    assert tx.events["Staked"].values()[1] == _amt


# Does the Withdrawn event fire?
@given(amount=strategy("uint256", max_value=(10 ** 18), min_value=(10 ** 1), exclude=0))
def test_withdrawn_event_fires(multi, alice, amount):
    multi.stake(amount, {"from": alice})
    tx = multi.withdraw(amount // 2, {"from": alice})
    assert tx.events["Withdrawn"].values()[0] == alice
    assert tx.events["Withdrawn"].values()[1] == amount // 2


# Does the RewardPaid event fire?
@given(amount=strategy("uint256", max_value=(10 ** 18), min_value=(10 ** 2)))
def test_reward_paid_event_fires(
    multi, accounts, base_token, reward_token, chain, alice, bob, amount
):
    tx = multi.getReward()

    reward_token.approve(multi, amount, {"from": bob})
    multi.setRewardsDistributor(reward_token, bob, {"from": alice})
    multi.notifyRewardAmount(reward_token, amount, {"from": bob})

    base_token.approve(multi, amount, {"from": bob})
    multi.stake(amount, {"from": bob})

    chain.mine(timedelta=60)
    value_earned = multi.earned(bob, reward_token)
    tx = multi.getReward({"from": bob})

    assert tx.events["Transfer"].values()[0] == multi
    assert tx.events["Transfer"].values()[1] == bob
    assert tx.events["RewardPaid"].values()[0] == bob
    assert tx.events["RewardPaid"].values()[1] == reward_token
    assert tx.events["RewardPaid"].values()[2] == value_earned


# Does the RewardsDurationUpdated event fire?
@given(duration=strategy("uint256", max_value=(10 ** 5), exclude=0))
def test_rewards_duration_fires(multi, alice, reward_token, duration):
    multi.setRewardsDistributor(reward_token, alice, {"from": alice})
    tx = multi.setRewardsDuration(reward_token, duration, {"from": alice})
    assert tx.events["RewardsDurationUpdated"].values()[0] == reward_token
    assert tx.events["RewardsDurationUpdated"].values()[1] == duration


# Does the Recovered event fire?
@given(amount=strategy("uint256", max_value=(10 ** 10), exclude=0))
def test_recovered_fires(multi, alice, reward_token, issue, amount, chain):
    chain.mine(timedelta=60)
    tx = multi.recoverERC20(reward_token, amount, {"from": alice})
    assert tx.events["Recovered"].values()[0] == reward_token
