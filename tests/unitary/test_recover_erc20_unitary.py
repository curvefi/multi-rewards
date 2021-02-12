#!/usr/bin/python3

import brownie
from brownie_tokens.template import ERC20


# Does the ERC20 recovery function produce expected behavior?
def test_recovery(multi, alice, err_token):
    assert err_token.balanceOf(alice) == 0
    multi.recoverERC20(err_token, 10 ** 18, {"from": alice})
    final_amount = err_token.balanceOf(alice)
    assert final_amount == 10 ** 18


# ERC20 function should fail on non-owner
def test_recovery_onlyowner(multi, reward_token, alice, bob, chain, issue):
    with brownie.reverts():
        multi.recoverERC20(reward_token, 10 ** 10, {"from": bob})


# Cannot withdraw the base token from ERC20 function
def test_no_withdraw_staking_token(multi, base_token, alice):
    with brownie.reverts():
        multi.recoverERC20(base_token, 10 ** 10, {"from": alice})


# Reward tokens can be withdrawn only by owner
def test_erc20_only_callable_owner(multi, err_token, issue, alice, charlie):
    with brownie.reverts("Only the contract owner may perform this action"):
        multi.recoverERC20(err_token, 10 ** 18, {"from": charlie})


# Assigned distributor cannot recover
def test_erc20_distributor_nonrecoverable(multi, reward_token, alice, bob):
    reward_token.approve(multi, 10 ** 18, {"from": bob})
    multi.setRewardsDistributor(reward_token, bob, {"from": alice})
    multi.notifyRewardAmount(reward_token, 10 ** 10, {"from": bob})

    with brownie.reverts("Only the contract owner may perform this action"):
        multi.recoverERC20(reward_token, 10 ** 10, {"from": bob})


# Only contract owner can withdraws
def test_erc20_only_owner_withdrawable(multi, reward_token, alice, bob):
    multi.setRewardsDistributor(reward_token, bob, {"from": alice})
    reward_token.approve(multi, 10 ** 10, {"from": bob})
    multi.notifyRewardAmount(reward_token, 10 ** 10, {"from": bob})

    with brownie.reverts("Only the contract owner may perform this action"):
        multi.recoverERC20(reward_token, 10 ** 10, {"from": bob})


# Can withdraw reward tokens
def test_erc20_withdrawable_after_set_distributor(multi, err_token, alice, bob):
    multi.setRewardsDistributor(err_token, bob, {"from": alice})

    tx = multi.recoverERC20(err_token, 10 ** 18, {"from": alice})
    assert tx.events["Recovered"].values()[0] == err_token


# Can be used to withdraw random tokens
def test_transfer_random_tokens(multi, alice):
    random_token = ERC20()
    random_token._mint_for_testing(alice, 10 ** 18, {"from": alice})
    random_token.transfer(multi, 10 ** 18, {"from": alice})
    assert random_token.balanceOf(alice) == 0
    multi.recoverERC20(random_token, 10 ** 18, {"from": alice})
    assert random_token.balanceOf(alice) == 10 ** 18


# Fail on token not assigned
def test_fail_random_tokens(multi, alice):
    random_token = ERC20()
    random_token._mint_for_testing(alice, 10 ** 18, {"from": alice})
    with brownie.reverts():
        multi.recoverERC20(random_token, 10 ** 18, {"from": alice})


# Fail on nonexistent token
def test_fail_nonexistent_tokens_with_amount(multi, alice, accounts):
    with brownie.reverts():
        multi.recoverERC20(accounts[0], 10 ** 18, {"from": alice})


# Fail on nonexistent tokens no amount
def test_fail_nonexistent_tokens_without_amount(multi, alice, accounts):
    with brownie.reverts():
        multi.recoverERC20(accounts[0], 0, {"from": alice})


# Withdraw of reward token effect on claiming
def test_no_withdraw_erc20_postreward(multi, alice, accounts, slow_token, base_token, chain):
    chain.mine(timedelta=60)
    with brownie.reverts("Cannot withdraw reward token"):
        multi.recoverERC20(slow_token, 10 ** 19, {"from": alice})


# Withdraw of reward token effect on claiming
def test_withdraw_erc20_then_claim(multi, alice, bob, accounts, slow_token, base_token, chain):
    base_token.approve(multi, base_token.balanceOf(bob), {"from": bob})
    multi.stake(base_token.balanceOf(bob), {"from": bob})
    chain.mine(timedelta=60)
    with brownie.reverts("Cannot withdraw reward token"):
        multi.recoverERC20(slow_token, 10 ** 19, {"from": alice})
