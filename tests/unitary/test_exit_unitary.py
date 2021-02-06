#!/usr/bin/python3
import brownie


# Confirm that a full withdraw occurs
def test_exit_withdraws(multi, alice, bob, base_token, reward_token, chain):
    amount = base_token.balanceOf(bob)
    base_token.approve(multi, amount, {"from": bob})
    multi.stake(amount, {"from": bob})
    assert base_token.balanceOf(bob) == 0
    assert multi.balanceOf(bob) == amount
    multi.exit({"from": bob})
    assert base_token.balanceOf(bob) == amount
    assert multi.balanceOf(bob) == 0


# Confirm that the full reward is claimed on exit
def test_exit_withdraws_reward(multi, alice, bob, base_token, reward_token, issue, chain):
    amount = base_token.balanceOf(bob)
    initial_reward_balance = reward_token.balanceOf(bob)

    base_token.approve(multi, amount, {"from": bob})
    multi.stake(amount, {"from": bob})
    assert base_token.balanceOf(bob) == 0
    assert multi.balanceOf(bob) == amount
    assert multi.earned(bob, reward_token) == 0
    chain.mine(timedelta=100)

    bob_earnings = multi.earned(bob, reward_token)
    assert bob_earnings > 0

    multi.exit({"from": bob})
    assert base_token.balanceOf(bob) == amount
    assert multi.balanceOf(bob) == 0
    assert reward_token.balanceOf(bob) == bob_earnings + initial_reward_balance


# Calling from a user with 0 balance should revert
def test_unstaked_reverts_on_exit(multi, alice, bob, base_token, reward_token, issue, chain):
    assert multi.balanceOf(bob) == 0
    with brownie.reverts():
        multi.exit({"from": bob})
