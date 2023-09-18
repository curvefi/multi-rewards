#!/usr/bin/python3

import pytest
from brownie_tokens.template import ERC20


# Reset
@pytest.fixture(scope="function", autouse=True)
def isolate(fn_isolation):
    pass


# Instantiate MultiFeeDistribution contract and approve the base token for transfers
@pytest.fixture(scope="module")
def multi(MultiFeeDistribution, mvault, alice, bob):
    _mr = MultiFeeDistribution.deploy({"from": alice})
    mvault.approve(_mr, 10 ** 19, {"from": alice})
    _mr.setStakingToken(mvault, {"from": alice}) # TODO: consider moving setStakingToken into it's own fixture to keep the multi fixture minimal
    return _mr


# Instantiate MockVault staking token contract, this basically serves the purpose of the base token(i.e. base_token) fixture
@pytest.fixture(scope="module")
def mvault(MockVault, accounts, alice):
    totalSupply = 6 * 10 ** 19 # each of the 6 account gets an equal share
    _mv = MockVault.deploy(totalSupply, {"from": alice})

    for idx in range(1, 5):
        _mv.transfer(accounts[idx], 10 ** 19, {"from": alice})

    return _mv


# Instantiate base token and provide 5 addresses a balance
@pytest.fixture(scope="module")
def base_token(accounts, alice):
    token = ERC20()
    token._mint_for_testing(alice, 10 ** 18, {"from": alice})
    for idx in range(1, 5):
        token._mint_for_testing(accounts[idx], 10 ** 19)
    return token


# Alice creates a reward token $RWD1 for Bob
@pytest.fixture(scope="module")
def reward_token(multi, accounts, alice, bob):
    _token = ERC20()
    _token._mint_for_testing(alice, 10 ** 19, {"from": alice})
    _token._mint_for_testing(bob, 10 ** 19)
    multi.setManagers([alice], {"from": alice})
    multi.addReward(_token, {"from": alice})
    return _token


# Alice creates a reward token $RWD1 for Bob
@pytest.fixture(scope="module")
def slow_token(multi, accounts, alice):
    slow_token = ERC20()
    amount = 10 ** 19
    slow_token._mint_for_testing(alice, amount)
    multi.setManagers([alice], {"from": alice})
    multi.addReward(slow_token, {"from": alice})
    return slow_token

@pytest.fixture(scope="module")
def issue_slow_token(multi, mvault, slow_token, alice, bob, chain):
    rewardAmount = 10 ** 18 # the initial staker will get this amount in it's entirely
    slow_token.transfer(mvault, rewardAmount, {"from": alice})
    mvault.setFarmingContract(multi)
    mvault.setRewardTokens([slow_token])
    mvault.setFarmingContract(multi)
    init_amount = slow_token.balanceOf(alice)
    return init_amount

# Alice creates a reward token $RWD2 for Charlie
@pytest.fixture(scope="module")
def reward_token2(multi, accounts, alice, charlie):
    _token = ERC20()
    _token._mint_for_testing(alice, 10 ** 18, {"from": alice})
    _token._mint_for_testing(charlie, 10 ** 18)
    multi.addReward(_token, {"from": alice})
    return _token


# Set a reward
@pytest.fixture(scope="module")
def issue(multi, mvault, reward_token, alice, bob, chain):
    rewardAmount = 10 ** 18 # the initial staker will get this amount in it's entirely
    reward_token.transfer(mvault, rewardAmount, {"from": alice})
    mvault.setFarmingContract(multi)
    mvault.setRewardTokens([reward_token])
    init_amount = reward_token.balanceOf(alice)
    return init_amount


# Set a reward
@pytest.fixture(scope="module")
def bob_token(multi, reward_token, alice, bob, chain):
    multi.setRewardsDistributor(reward_token, bob, {"from": alice})
    reward_token.approve(multi, 10 ** 18, {"from": bob})
    multi.notifyRewardAmount(reward_token, 10 ** 18, {"from": bob})
    return reward_token


# Transfer a random token by err
@pytest.fixture(scope="module")
def err_token(multi, reward_token, alice, bob, chain):
    err_token = ERC20()
    amount = 10 ** 18
    err_token._mint_for_testing(alice, amount, {"from": alice})
    err_token.approve(multi, amount, {"from": alice})
    err_token.transfer(multi, amount, {"from": alice})

    return err_token


# Hi Alice
@pytest.fixture(scope="session")
def alice(accounts):
    yield accounts[0]


# Hey-a Bob
@pytest.fixture(scope="session")
def bob(accounts):
    yield accounts[1]


# Don't forget Charlie
@pytest.fixture(scope="session")
def charlie(accounts):
    yield accounts[2]

@pytest.fixture(scope="session")
def manager1(accounts):
    yield accounts[3]
