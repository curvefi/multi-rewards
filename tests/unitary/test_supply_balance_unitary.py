##!/usr/bin/python3

import pytest


# Initial accounts at zero
@pytest.mark.parametrize("idx", range(5))
def test_initial_approval_is_zero(multi, accounts, idx):
    assert multi.userData(accounts[idx])["tokenAmount"] == 0


# No supply at start
def test_no_initial_supply(multi):
    assert multi.totalStakes() == 0


# Starting balance for owner is zero
def test_initial_stake_is_zero(multi, accounts, alice):
    assert multi.userData(alice)["tokenAmount"] == 0


# No owner earnings at start
def test_no_initial_earnings_alice(multi, reward_token, alice):
    (rewardTokens, rewardAmounts) = multi.claimableRewards(alice)
    for rewardToken, rewardAmount in zip(rewardTokens, rewardAmounts):
        if rewardToken == reward_token:
            assert rewardAmount == 0


# No bob earnings at start
def test_no_initial_earnings_bob(multi, reward_token, bob):
    (rewardTokens, rewardAmounts) = multi.claimableRewards(bob)
    for rewardToken, rewardAmount in zip(rewardTokens, rewardAmounts):
        if rewardToken == reward_token:
            assert rewardAmount == 0


# No charlie earnings at start
def test_no_initial_earnings_charlie(multi, reward_token, charlie):
    (rewardTokens, rewardAmounts) = multi.claimableRewards(charlie)
    for rewardToken, rewardAmount in zip(rewardTokens, rewardAmounts):
        if rewardToken == reward_token:
            assert rewardAmount == 0


# Ensure total supply and balance update correctly
def test_supply_balance_updates(multi, reward_token, alice):
    multi.stake(10000, alice, {"from": alice})
    assert multi.userData(alice)["tokenAmount"] == 10000
    assert multi.totalStakes() == 10000
