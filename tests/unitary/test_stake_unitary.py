#!/usr/bin/python3

import brownie
from brownie_tokens.template import ERC20
from utils import withCustomError


# Cannot stake zero
def test_cannot_stake_zero(multi, alice):
    with brownie.reverts(withCustomError("InvalidAmount()")):
        multi.stake(0, alice, {"from": alice})


# Can owner stake?
def test_owner_place_stake(multi, reward_token, alice):
    multi.stake(10000, alice, {"from": alice})
    assert multi.userData(alice)["tokenAmount"] > 0

# NOTE: if this test is run by itself, it succeeds, but when run with other tests it fails. This is likely a fixture issue?
# Will n staked addresses all earn rewards?
def test_n_rewards(multi, accounts, alice, mvault, chain):

    multi.setManagers([alice], {"from": alice})

    mvault.setFarmingContract(multi)

    n = 5
    _tokens = {}
    for i in range(n):
        _tokens[i] = ERC20()
        _tokens[i]._mint_for_testing(accounts[i], 10 ** 18)
        _tokens[i].approve(multi, 10 ** 18, {"from": accounts[i]})
        mvault.approve(multi, 10 ** 18, {"from": accounts[i]})

        # NOTE: Gamma staking contract seems to not award 1st staker any of the 1st reward token
        # hence add the 1st reward token and then stake
        if (i == 0):
            multi.addReward(_tokens[i], {"from": alice})
            mvault.setRewardTokens([_tokens[i]])
            _tokens[i].transfer(mvault, 10 ** 10, {"from": accounts[i]})

        multi.stake(10000, accounts[i], {"from": accounts[i]})

        if (i > 0):
            multi.addReward(_tokens[i], {"from": alice})
            mvault.setRewardTokens([_tokens[i]])
            _tokens[i].transfer(mvault, 10 ** 10, {"from": accounts[i]})

        # NOTE: double stake to trigger rewardData to update
        multi.stake(10000, accounts[i], {"from": accounts[i]})

    chain.mine(timedelta=120)
    for accountIndex in range(n):
        (rewardTokens, rewardAmounts) = multi.claimableRewards(accounts[accountIndex])
        for tokenIndex in range(n):
            # an account should only have rewards from after it staked
            if (accountIndex > tokenIndex):
                continue
            assert rewardAmounts[accountIndex] > 0


# Ensure total supply and balance transfer from caller to contract
def test_supply_balance_updates(multi, mvault, alice):
    amount = 10 ** 10
    init_val = mvault.balanceOf(alice)
    multi.stake(amount, alice, {"from": alice})
    assert mvault.balanceOf(alice) == init_val - amount
    assert multi.userData(alice)["tokenAmount"] == amount
    assert multi.totalStakes() == amount


# Call reverts on insufficient token balance
def test_staking_reverts_on_balance(multi, mvault, alice):
    with brownie.reverts():
        multi.stake(mvault.balanceOf(alice) + 1, alice, {"from": alice})
