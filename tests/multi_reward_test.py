import pytest


@pytest.fixture(scope="module", autouse=True)
def staking_token(StakingToken, accounts):
    yield accounts[0].deploy(StakingToken)


@pytest.fixture(scope="module", autouse=True)
def test1_token(Test1Token, accounts):
    yield accounts[0].deploy(Test1Token)


@pytest.fixture(scope="module", autouse=True)
def test2_token(Test2Token, accounts):
    yield accounts[0].deploy(Test2Token)


@pytest.fixture(scope="module")
def multi_reward_contract(MultiRewards, staking_token, accounts):
    yield accounts[0].deploy(MultiRewards, accounts[0], staking_token.address)


def test_add_reward_token(multi_reward_contract, test1_token, test2_token, accounts):
    multi_reward_contract.addReward(test1_token.address, accounts[0], 3600 * 24 * 30)
    reward1 = multi_reward_contract.rewardData(test1_token.address)
    assert reward1[0] == accounts[0]

    multi_reward_contract.addReward(test2_token.address, accounts[0], 3600 * 24 * 30)
    reward2 = multi_reward_contract.rewardData(test2_token.address)
    assert reward2[0] == accounts[0]


def test_user_stake(staking_token, multi_reward_contract, accounts, web3):
    acc1stake = web3.toWei(10000, "ether")
    staking_token.transfer(accounts[1], acc1stake)
    staking_token.approve(multi_reward_contract.address, acc1stake, {'from': accounts[1]})
    multi_reward_contract.stake(acc1stake, {'from': accounts[1]})
    assert multi_reward_contract.balanceOf(accounts[1]) == acc1stake

    acc2stake = web3.toWei(2500, "ether")
    staking_token.transfer(accounts[2], acc2stake)
    staking_token.approve(multi_reward_contract.address, acc2stake, {'from': accounts[2]})
    multi_reward_contract.stake(acc2stake, {'from': accounts[2]})
    assert multi_reward_contract.balanceOf(accounts[2]) == acc2stake

    acc3stake = web3.toWei(5000, "ether")
    staking_token.transfer(accounts[3], acc3stake)
    staking_token.approve(multi_reward_contract.address, acc3stake, {'from': accounts[3]})
    multi_reward_contract.stake(acc3stake, {'from': accounts[3]})
    assert multi_reward_contract.balanceOf(accounts[3]) == acc3stake


def test_notify_calculations(test1_token, test2_token, multi_reward_contract, accounts, web3, chain):
    time_for_full_reward = 3600 * 24 * 30
    reward_calc_time = 3600 * 24 * 15
    test1reward = web3.toWei(10000, 'ether')
    test2reward = web3.toWei(500000, 'ether')
    test1_token.approve(multi_reward_contract.address, test1reward)
    test2_token.approve(multi_reward_contract.address, test2reward)
    multi_reward_contract.notifyRewardAmount(test1_token.address, test1reward)
    multi_reward_contract.notifyRewardAmount(test2_token.address, test2reward)

    chain.sleep(reward_calc_time)
    chain.mine()

    earned1test1 = multi_reward_contract.earned(accounts[1], test1_token.address)
    earned1test2 = multi_reward_contract.earned(accounts[1], test2_token.address)

    earned2test1 = multi_reward_contract.earned(accounts[2], test1_token.address)
    earned2test2 = multi_reward_contract.earned(accounts[2], test2_token.address)

    earned3test1 = multi_reward_contract.earned(accounts[3], test1_token.address)
    earned3test2 = multi_reward_contract.earned(accounts[3], test2_token.address)

    acc1stake = web3.toWei(10000, "ether")
    acc2stake = web3.toWei(2500, "ether")
    acc3stake = web3.toWei(5000, "ether")

    totalSupply = multi_reward_contract.totalSupply()
    divisor = reward_calc_time / time_for_full_reward

    assert float(earned1test1) == float(acc1stake / totalSupply * test1reward * divisor)
    assert float(earned1test2) == float(acc1stake / totalSupply * test2reward * divisor)
    assert float(earned2test1) == float(acc2stake / totalSupply * test1reward * divisor)
    assert float(earned2test2) == float(acc2stake / totalSupply * test2reward * divisor)
    assert float(earned3test1) == float(acc3stake / totalSupply * test1reward * divisor)
    assert float(earned3test2) == float(acc3stake / totalSupply * test2reward * divisor)

    reward_calc_time = 3600 * 24 * 30
    chain.sleep(reward_calc_time)
    chain.mine()

    earned1test1 = multi_reward_contract.earned(accounts[1], test1_token.address)
    earned1test2 = multi_reward_contract.earned(accounts[1], test2_token.address)

    earned2test1 = multi_reward_contract.earned(accounts[2], test1_token.address)
    earned2test2 = multi_reward_contract.earned(accounts[2], test2_token.address)

    earned3test1 = multi_reward_contract.earned(accounts[3], test1_token.address)
    earned3test2 = multi_reward_contract.earned(accounts[3], test2_token.address)

    acc1stake = web3.toWei(10000, "ether")
    acc2stake = web3.toWei(2500, "ether")
    acc3stake = web3.toWei(5000, "ether")

    totalSupply = multi_reward_contract.totalSupply()
    divisor = reward_calc_time / time_for_full_reward
    assert float(earned1test1) == float(acc1stake / totalSupply * test1reward * divisor)
    assert float(earned1test2) == float(acc1stake / totalSupply * test2reward * divisor)
    assert float(earned2test1) == float(acc2stake / totalSupply * test1reward * divisor)
    assert float(earned2test2) == float(acc2stake / totalSupply * test2reward * divisor)
    assert float(earned3test1) == float(acc3stake / totalSupply * test1reward * divisor)
    assert float(earned3test2) == float(acc3stake / totalSupply * test2reward * divisor)

    # assert multi_reward_contract.getRewardForDuration(test1_token) == test1reward


def test_get_rewards(test1_token, test2_token, multi_reward_contract, accounts):
    earned1test1 = multi_reward_contract.earned(accounts[1], test1_token.address)
    earned1test2 = multi_reward_contract.earned(accounts[1], test2_token.address)

    earned2test1 = multi_reward_contract.earned(accounts[2], test1_token.address)
    earned2test2 = multi_reward_contract.earned(accounts[2], test2_token.address)

    earned3test1 = multi_reward_contract.earned(accounts[3], test1_token.address)
    earned3test2 = multi_reward_contract.earned(accounts[3], test2_token.address)

    multi_reward_contract.getReward({'from': accounts[1]})
    multi_reward_contract.getReward({'from': accounts[2]})
    multi_reward_contract.getReward({'from': accounts[3]})

    assert float(test1_token.balanceOf(accounts[1])) == float(earned1test1)
    assert float(test2_token.balanceOf(accounts[1])) == float(earned1test2)

    assert float(test1_token.balanceOf(accounts[2])) == float(earned2test1)
    assert float(test2_token.balanceOf(accounts[2])) == float(earned2test2)

    assert float(test1_token.balanceOf(accounts[3])) == float(earned3test1)
    assert float(test2_token.balanceOf(accounts[3])) == float(earned3test2)

    earned1test1 = multi_reward_contract.earned(accounts[1], test1_token.address)
    earned1test2 = multi_reward_contract.earned(accounts[1], test2_token.address)

    earned2test1 = multi_reward_contract.earned(accounts[2], test1_token.address)
    earned2test2 = multi_reward_contract.earned(accounts[2], test2_token.address)

    earned3test1 = multi_reward_contract.earned(accounts[3], test1_token.address)
    earned3test2 = multi_reward_contract.earned(accounts[3], test2_token.address)

    assert earned1test1 == 0
    assert earned1test2 == 0
    assert earned2test1 == 0
    assert earned2test2 == 0
    assert earned3test1 == 0
    assert earned3test2 == 0


def test_exit_with_correct_amounts(staking_token, test1_token, test2_token, multi_reward_contract, accounts, web3, chain):
    reward_calc_time = 3600 * 24 * 30
    test1reward = web3.toWei(280000, 'ether')
    test2reward = web3.toWei(34600, 'ether')
    test1_token.approve(multi_reward_contract.address, test1reward)
    test2_token.approve(multi_reward_contract.address, test2reward)
    multi_reward_contract.notifyRewardAmount(test1_token.address, test1reward)
    multi_reward_contract.notifyRewardAmount(test2_token.address, test2reward)

    chain.sleep(reward_calc_time)
    chain.mine()

    acc1stake = web3.toWei(10000, "ether")
    acc2stake = web3.toWei(2500, "ether")
    acc3stake = web3.toWei(5000, "ether")

    multi_reward_contract.exit({'from': accounts[1]})
    multi_reward_contract.exit({'from': accounts[2]})
    multi_reward_contract.exit({'from': accounts[3]})

    assert staking_token.balanceOf(accounts[1]) == acc1stake
    assert staking_token.balanceOf(accounts[2]) == acc2stake
    assert staking_token.balanceOf(accounts[3]) == acc3stake

    assert multi_reward_contract.balanceOf(accounts[1]) == 0
    assert multi_reward_contract.balanceOf(accounts[2]) == 0
    assert multi_reward_contract.balanceOf(accounts[3]) == 0
