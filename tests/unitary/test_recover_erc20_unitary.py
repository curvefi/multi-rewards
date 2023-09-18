#!/usr/bin/python3

import brownie
from brownie_tokens.template import ERC20
from utils import withCustomError


# Does the ERC20 recovery function produce expected behavior?
def test_recovery(multi, alice, err_token):
    assert err_token.balanceOf(alice) == 0
    multi.recoverERC20(err_token, 10 ** 18, {"from": alice})
    final_amount = err_token.balanceOf(alice)
    assert final_amount == 10 ** 18


# ERC20 function should fail on non-owner
def test_recovery_onlyowner(multi, reward_token, alice, bob, chain, issue):
    with brownie.reverts('Ownable: caller is not the owner'):
        multi.recoverERC20(reward_token, 10 ** 10, {"from": bob})


# Cannot withdraw the base token from ERC20 function
def test_no_withdraw_staking_token(multi, mvault, alice):

    amount = 10 ** 10

    mvault.approve(multi, amount, {"from": alice})
    multi.stake(amount, alice, {"from": alice})

    with brownie.reverts(withCustomError("IsStakingToken()")):
        multi.recoverERC20(mvault, amount, {"from": alice})


# Reward tokens can be withdrawn only by owner
def test_erc20_only_callable_owner(multi, err_token, issue, alice, charlie):
    with brownie.reverts("Ownable: caller is not the owner"):
        multi.recoverERC20(err_token, 10 ** 18, {"from": charlie})


# Cannot recover reward tokens on an active reward
def test_erc20_rewards_nonrecoverable(multi, mvault, reward_token, alice, bob, issue, chain):
    amount = 10 ** 10
    # make reward active and also have the rewardData.lastTimeUpdated update
    # for some reason Gamma didn't update lastTimeUpdated on the initial stake
    mvault.approve(multi, amount, {"from": alice})
    tx = multi.stake(amount, alice, {"from": alice})
    mvault.approve(multi, amount, {"from": bob})
    tx = multi.stake(amount, bob, {"from": bob})

    with brownie.reverts(withCustomError("ActiveReward()")):
        multi.recoverERC20(reward_token, amount, {"from": alice})


# Only contract owner can withdraws
def test_erc20_only_owner_withdrawable(multi, reward_token, alice, bob, issue):
    with brownie.reverts("Ownable: caller is not the owner"):
        multi.recoverERC20(reward_token, 10 ** 10, {"from": bob})


# NOTE: this test case is not applicable to Gamma's staking contract which does not have a distributor
# # Can withdraw reward tokens
# def test_erc20_withdrawable_after_set_distributor(multi, err_token, alice, bob):
#     multi.setRewardsDistributor(err_token, bob, {"from": alice})

#     tx = multi.recoverERC20(err_token, 10 ** 18, {"from": alice})
#     assert tx.events["Recovered"].values()[0] == err_token


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


# NOTE: already tested in test_erc20_rewards_nonrecoverable()
# # Withdraw of reward token effect on claiming
# def test_no_withdraw_erc20_postreward(multi, alice, accounts, slow_token, base_token, chain):
#     chain.mine(timedelta=60)
#     with brownie.reverts("Cannot withdraw reward token"):
#         multi.recoverERC20(slow_token, 10 ** 19, {"from": alice})


# NOTE: already tested in test_erc20_rewards_nonrecoverable()
# # Withdraw of reward token effect on claiming
# def test_withdraw_erc20_then_claim(multi, alice, bob, accounts, slow_token, base_token, chain):
#     base_token.approve(multi, base_token.balanceOf(bob), {"from": bob})
#     multi.stake(base_token.balanceOf(bob), {"from": bob})
#     chain.mine(timedelta=60)
#     with brownie.reverts("Cannot withdraw reward token"):
#         multi.recoverERC20(slow_token, 10 ** 19, {"from": alice})
