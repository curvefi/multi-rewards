#!/usr/bin/python3
import brownie
from utils import withCustomError


# Confirm that a full withdraw occurs
def test_unstake_withdraws(multi, alice, bob, mvault, reward_token, chain):
    amount = mvault.balanceOf(bob)
    mvault.approve(multi, amount, {"from": bob})
    multi.stake(amount, bob, {"from": bob})
    assert mvault.balanceOf(bob) == 0
    assert multi.userData(bob)["tokenAmount"] == amount
    multi.unstake(amount, {"from": bob})
    assert mvault.balanceOf(bob) == amount
    assert multi.userData(bob)["tokenAmount"] == 0


# Confirm that the full reward is claimed on exit
def test_unstake_withdraws_reward(multi, alice, bob, mvault, reward_token, issue, chain):
    mvault_initial_reward_balance = reward_token.balanceOf(mvault) # 1st staker claims the entire reward balance

    amount = mvault.balanceOf(bob)
    bob_initial_reward_balance = reward_token.balanceOf(bob)

    mvault.approve(multi, amount, {"from": bob})
    multi.stake(amount, bob, {"from": bob})
    assert mvault.balanceOf(bob) == 0
    assert multi.userData(bob)["tokenAmount"] == amount

    (rewardTokens, rewardAmounts) = multi.claimableRewards(bob)
    assert rewardAmounts[0] == 0
    assert rewardTokens[0] == reward_token

    rewardAmount = 10 ** 18
    reward_token.transfer(mvault, rewardAmount, {"from": alice})

    multi.unstake(amount, {"from": bob})
    (rewardTokens, rewardAmounts) = multi.claimableRewards(bob)
    assert rewardAmounts[0] == (rewardAmount + mvault_initial_reward_balance)

    bob_earnings = rewardAmount # since bob was the only staker, bob gets the entire rewardAmount(including the entire amount that was collected from mvault when he initially staked)

    multi.getAllRewards({"from": bob})
    assert mvault.balanceOf(bob) == amount
    assert multi.userData(bob)["tokenAmount"] == 0
    assert reward_token.balanceOf(bob) == (bob_earnings + bob_initial_reward_balance + mvault_initial_reward_balance)


# Calling from a user with an amount that exceeds the current staked amount should revert
def test_unstake_reverts_on_invalid_amount(multi, alice, bob, base_token, reward_token, issue, chain):
    assert multi.userData(bob)["tokenAmount"] == 0
    with brownie.reverts(withCustomError("InvalidAmount()")):
        multi.unstake(1, {"from": bob})

