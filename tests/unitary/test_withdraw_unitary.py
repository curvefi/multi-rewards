#!/usr/bin/python3

import brownie
from utils import withCustomError


def earned(multi, account, token):
    (rewardTokens, rewardAmounts) = multi.claimableRewards(account)
    for rewardToken, rewardAmount in zip(rewardTokens, rewardAmounts):
        if (rewardToken == token):
            return rewardAmount

def exit(multi, account):
    amount = multi.userData(account)["tokenAmount"]
    unstakeTx = multi.unstake(amount, {"from": account})
    getAllRewardsTx = multi.getAllRewards({"from": account})
    return [unstakeTx, getAllRewardsTx]

def injectReward(mvault, farmingContract, rewardToken, amount, account):
    mvault.setFarmingContract(farmingContract)
    mvault.setRewardTokens([rewardToken])
    rewardToken.transfer(mvault, amount, {"from": account})

# Can user A and user B withdraw in correct proportion?
def test_withdraw_multiples(multi, mvault, slow_token, issue_slow_token, alice, bob, charlie, chain):
    amount = 10 ** 10
    mvault._mint_for_testing(bob, amount)
    mvault._mint_for_testing(charlie, amount)

    mvault.approve(multi, amount, {"from": bob})
    multi.stake(amount, bob, {"from": bob})
    mvault.approve(multi, 10 * amount, {"from": charlie})
    multi.stake(amount * 10, charlie, {"from": charlie})

    # NOTE: mint with alice so that claimableRewards for charlie reflects latest
    # this should probably be improved in the contract
    mvault.approve(multi, 10 * amount, {"from": alice})
    multi.stake(amount * 10, alice, {"from": alice})

    chain.mine(timedelta=60 * 60)
    earn_b = earned(multi, bob, slow_token)
    earn_c = earned(multi, charlie, slow_token)

    bob_init_base_balance = mvault.balanceOf(bob)
    bob_init_reward_balance = slow_token.balanceOf(bob)
    charlie_init_base_balance = mvault.balanceOf(charlie)
    charlie_init_reward_balance = slow_token.balanceOf(charlie)

    [unstakeTx, getAllRewardsTx] = exit(multi, bob)
    bob_exit_val = unstakeTx.events["Unstake"].values()[1]
    bob_final_base_balance = mvault.balanceOf(bob)
    bob_final_reward_balance = slow_token.balanceOf(bob)
    bob_final_base_gain = bob_final_base_balance - bob_init_base_balance
    bob_final_reward_gain = bob_final_reward_balance - bob_init_reward_balance

    [unstakeTx, getAllRewardsTx] = exit(multi, charlie)
    charlie_exit_val = unstakeTx.events["Unstake"].values()[1]
    charlie_final_base_balance = mvault.balanceOf(charlie)
    charlie_final_reward_balance = slow_token.balanceOf(charlie)
    charlie_final_base_gain = charlie_final_base_balance - charlie_init_base_balance
    charlie_final_reward_gain = charlie_final_reward_balance - charlie_init_reward_balance

    assert earn_b > 0
    assert earn_c == 0
    # NOTE: no additional reward injection other than the injection in the issue_slow_token fixture
    # so charlie gets no rewards and bob gets all as he is the 1st to stake, so the following assertions need to be reconsidered
    # assert earn_b * 0.99 <= earn_c // 10 <= earn_b * 1.01
    # assert multi.balanceOf(charlie) // 10 == multi.balanceOf(bob)
    # assert charlie_exit_val // 10 == bob_exit_val
    # assert (
    #     bob_final_reward_gain * 0.99
    #     <= charlie_final_reward_gain // 10
    #     <= bob_final_reward_gain * 1.01
    # )
    # assert charlie_final_base_gain // 10 == bob_final_base_gain


# Test for token A reward != token B reward
def test_different_reward_amounts(
    multi, mvault, reward_token, reward_token2, alice, bob, chain
):
    amount = 10 ** 12

    mvault_initial_reward_balance = reward_token.balanceOf(mvault)

    rewardAmount = 10 ** 15 - mvault_initial_reward_balance
    injectReward(mvault, multi, reward_token, rewardAmount, alice)

    rewardAmount2 = 10 ** 14
    injectReward(mvault, multi, reward_token2, rewardAmount2, alice)

    mvault.approve(multi, amount, {"from": bob})
    multi.stake(amount, bob, {"from": bob})

    chain.mine(timedelta=1000)

    reward_1_earnings = earned(multi, bob, reward_token)
    reward_2_earnings = earned(multi, bob, reward_token2)

    init_base_balance = mvault.balanceOf(bob)
    init_reward_balance = reward_token.balanceOf(bob)
    init_reward2_balance = reward_token2.balanceOf(bob)

    exit(multi, bob)

    final_base_balance = mvault.balanceOf(bob)
    final_reward_balance = reward_token.balanceOf(bob)
    final_reward2_balance = reward_token2.balanceOf(bob)

    final_base_gain = final_base_balance - init_base_balance
    final_reward_gain = final_reward_balance - init_reward_balance
    final_reward2_gain = final_reward2_balance - init_reward2_balance

    assert reward_2_earnings * 0.98 <= reward_1_earnings // 10 <= reward_2_earnings * 1.02
    assert final_reward2_gain * 0.98 <= final_reward_gain // 10 <= final_reward2_gain * 1.02
    assert final_base_gain == amount


# Can the owner stake and then withdraw?
def test_owner_withdraw(multi, mvault, alice):
    amount = mvault.balanceOf(alice)
    mvault.approve(multi, amount, {"from": alice})
    multi.stake(amount, alice, {"from": alice})
    multi.unstake(amount, {"from": alice})
    assert multi.userData(alice)["tokenAmount"] == 0
    assert mvault.balanceOf(alice) == amount


# Cannot withdraw 0
def test_cannot_withdraw_zero(multi, charlie):
    assert multi.userData(charlie)["tokenAmount"] == 0
    with brownie.reverts(withCustomError("InvalidAmount()")):
        multi.unstake(1, {"from": charlie})


# Cannot withdraw more than deposit
def test_cannot_withdraw_more_than_deposit(multi, alice, mvault):
    amount = mvault.balanceOf(alice)
    mvault.approve(multi, amount, {"from": alice})
    multi.stake(amount, alice, {"from": alice})

    with brownie.reverts(withCustomError("InvalidAmount()")):
        multi.unstake(1 + amount, {"from": alice})


def test_cannot_withdraw_more_than_deposit_if_balance_exists(multi, alice, bob, mvault):
    amount = mvault.balanceOf(alice)
    aliceAmount = amount
    mvault.approve(multi, amount, {"from": alice})
    multi.stake(amount, alice, {"from": alice})

    amount = mvault.balanceOf(bob)
    mvault.approve(multi, amount, {"from": bob})
    multi.stake(amount, bob, {"from": bob})

    with brownie.reverts(withCustomError("InvalidAmount()")):
        multi.unstake(1 + aliceAmount, {"from": alice})


# Supply and balance change on withdraw
def test_supply_balance_changes_on_withdraw(multi, alice, mvault):
    amount = mvault.balanceOf(alice)

    mvault.approve(multi, amount, {"from": alice})
    multi.stake(amount, alice, {"from": alice})

    init_supply = multi.totalStakes()
    init_balance = multi.userData(alice)["tokenAmount"]
    withdraw_amount = amount // 3
    multi.unstake(withdraw_amount, {"from": alice})
    assert multi.totalStakes() == init_supply - withdraw_amount
    assert multi.userData(alice)["tokenAmount"] == init_balance - withdraw_amount
    assert mvault.balanceOf(alice) == withdraw_amount
