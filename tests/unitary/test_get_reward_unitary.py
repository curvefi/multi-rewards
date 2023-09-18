#!/usr/bin/python3


# Can user retrieve reward after rewards have been collected from the Hypervisor(i.e. staking token which is the vault)
def test_get_reward(multi, mvault, reward_token, alice, bob, issue, chain):

    mvault_initial_reward_balance = reward_token.balanceOf(mvault)

    amount = 10 ** 10
    init_reward_balance = reward_token.balanceOf(alice)
    mvault.approve(multi, amount, {"from": alice})
    multi.stake(amount, alice, {"from": alice})

    # TODO: Investigate why for some reason it the claimableRewards doesn't equal the mvault_initial_reward_balance
    # however it should since stake should have claimed the rewards to multi
    # but it's not too big an issue as alice still gets mvault_initial_reward_balance at the very end
    # (rewardTokens, rewardAmountsInitial) = multi.claimableRewards(alice)
    # assert rewardAmountsInitial[0] == mvault_initial_reward_balance

    rewardAmount = 10 ** 17
    reward_token.transfer(mvault, rewardAmount, {"from": bob})

    # bob stakes which should trigger an increase to the value of Alice's stake as the amount of rewards accumulated in the farming contract increased
    mvault.approve(multi, amount, {"from": bob})
    multi.stake(amount, bob, {"from": bob})

    (rewardTokens, rewardAmountsIntermediate) = multi.claimableRewards(alice)
    earnings = rewardAmountsIntermediate[0]
    assert earnings == (mvault_initial_reward_balance + rewardAmount)

    tx = multi.getReward(alice, [reward_token], {"from": alice})
    final_reward_balance = reward_token.balanceOf(alice)
    assert final_reward_balance - init_reward_balance == earnings


# Reward per token over many cycles?
def test_multiuser_reward_per_token_paid(multi, mvault, reward_token, alice, bob, issue, chain):
    mvault_initial_reward_balance = reward_token.balanceOf(mvault)
    reward_token._mint_for_testing(alice, 10 ** 18, {"from": alice})

    stakeAmount = 10 ** 10
    mvault.approve(multi, stakeAmount, {"from": alice})
    multi.stake(stakeAmount, alice, {"from": alice})

    for i in range(5):
        last_val = multi.getUserRewardPerToken(alice, reward_token)

        rewardAmount = 10 ** 10
        reward_token.transfer(mvault, rewardAmount, {"from": alice})

        (rewardTokens, rewardAmounts) = multi.claimableRewards(alice)

        earnings = rewardAmounts[0] + rewardAmount
        if (i == 0):
            earnings = earnings + mvault_initial_reward_balance

        tx = multi.getReward(alice, [reward_token], {"from": alice})
        assert tx.events["RewardPaid"].values()[2] == earnings
        assert multi.getUserRewardPerToken(alice, reward_token) > last_val


# User should not be able to withdraw a reward if empty
def test_cannot_get_empty_reward(multi, reward_token, alice, chain):
    init_amount = reward_token.balanceOf(alice)
    chain.mine(timedelta=60)
    multi.getReward(alice, [reward_token], {"from": alice})
    final_amount = reward_token.balanceOf(alice)
    assert init_amount == final_amount


# User should not be able to withdraw a reward if empty
def test_no_action_on_empty_reward(multi, reward_token, charlie):
    tx = multi.getReward(charlie, [reward_token], {"from": charlie})
    assert "RewardPaid" not in tx.events


# Call from a user who is staked should receive the correct amount of tokens
def test_staked_token_value(multi, mvault, reward_token, alice, charlie, issue, chain):

    mvault_initial_reward_balance = reward_token.balanceOf(mvault)

    amount = mvault.balanceOf(charlie)
    reward_init_bal = reward_token.balanceOf(charlie)
    mvault.approve(multi, amount, {"from": charlie})
    multi.stake(amount, charlie, {"from": charlie})
    assert mvault.balanceOf(charlie) == 0
    assert multi.userData(charlie)["tokenAmount"] == amount

    chain.mine(timedelta=60)
    reward_per_token = multi.rewardData(reward_token)["rewardPerToken"]
    earned_calc = reward_per_token * amount // 10 ** 18
    (rewardTokens, rewardAmounts) = multi.claimableRewards(charlie)
    earnings = rewardAmounts[0]
    assert earned_calc == earnings

    expectedRewardAmount = (earned_calc + mvault_initial_reward_balance)

    tx = multi.getReward(charlie, [reward_token], {"from": charlie})
    assert tx.events["RewardPaid"].values()[2] == expectedRewardAmount
    assert reward_token.balanceOf(charlie) - reward_init_bal == expectedRewardAmount


# User at outset has no earnings
def test_fresh_user_no_earnings(multi, reward_token, charlie, issue):
    (rewardTokens, rewardAmounts) = multi.claimableRewards(charlie)
    assert rewardAmounts[0] == 0


# User has no earnings after staking
def test_no_earnings_upon_staking(multi, reward_token, mvault, charlie, issue):
    # TODO: actually charlie does have rewards from the starting positive balance of the farming contract
    # however for some reason claimableRewards returns 0, but if charlie were to do another action they will claim that starting balance
    amount = mvault.balanceOf(charlie)
    mvault.approve(multi, amount, {"from": charlie})
    multi.stake(amount, charlie, {"from": charlie})
    (rewardTokens, rewardAmounts) = multi.claimableRewards(charlie)
    assert rewardAmounts[0] == 0


# NOTE: This test case is not relevant to Gamma as rewards are not distributed continuously over time, but are emission/drip based
# # User has earnings after staking and waiting
# def test_user_accrues_rewards(multi, reward_token, mvault, charlie, issue, chain):
#     amount = mvault.balanceOf(charlie)
#     mvault.approve(multi, amount, {"from": charlie})
#     multi.stake(amount, charlie, {"from": charlie})
#     chain.mine(timedelta=60)
#     period = (
#         multi.lastTimeRewardApplicable(reward_token)
#         - multi.rewardData(reward_token)["lastUpdateTime"]
#     )
#     calc_earn = period * (10 ** 18 / 60)
#     assert calc_earn * 0.99 <= multi.earned(charlie, reward_token) <= calc_earn * 1.01


# User has no rewards after claiming rewards
def test_no_earnings_post_withdrawal(
    multi, reward_token, slow_token, mvault, alice, charlie, issue, chain
):
    amount = mvault.balanceOf(charlie)
    mvault.approve(multi, amount, {"from": charlie})
    multi.stake(amount, charlie, {"from": charlie})
    chain.mine(timedelta=30)

    tx = multi.getReward(charlie, [reward_token], {"from": charlie})
    assert tx.events["RewardPaid"].values()[2] > 0

    chain.mine(timedelta=30)
    (rewardTokens, rewardAmounts) = multi.claimableRewards(charlie)
    assert rewardAmounts[0] == 0


# Call from a user who is staked should receive the correct amount of tokens
# Also confirm earnings at various stages
def test_staked_tokens_multi_durations(
    multi, reward_token, slow_token, mvault, alice, charlie, issue, chain
):

    mvault_initial_reward_balance = reward_token.balanceOf(mvault)

    reward_init_bal = reward_token.balanceOf(charlie)
    slow_init_bal = slow_token.balanceOf(charlie)

    amount = mvault.balanceOf(charlie)
    mvault.approve(multi, amount, {"from": charlie})
    multi.stake(amount, charlie, {"from": charlie})

    precision = 10 ** 50

    for i in range(1):
        reward_init_bal = reward_token.balanceOf(charlie)
        slow_init_bal = slow_token.balanceOf(charlie)
        charlie_paid_reward = multi.getUserRewardPerToken(charlie, reward_token)
        charlie_paid_slow = multi.getUserRewardPerToken(charlie, slow_token)
        chain.mine(timedelta=30)

        reward_per = multi.rewardData(reward_token)["rewardPerToken"]
        slow_per = multi.rewardData(slow_token)["rewardPerToken"]
        reward_calc = (amount * (reward_per - charlie_paid_reward)) // precision
        slow_calc = (amount * (slow_per - charlie_paid_slow)) // precision

        (rewardTokens, rewardAmounts) = multi.claimableRewards(charlie)

        assert reward_calc == rewardAmounts[0]
        assert slow_calc == rewardAmounts[1]

        multi.getReward(charlie, [reward_token, slow_token], {"from": charlie})

        # Reward may have changed in the second it takes to getReward
        reward_per_act = multi.rewardData(reward_token)["rewardPerToken"]
        slow_per_act = multi.rewardData(slow_token)["rewardPerToken"]
        reward_calc_act = (amount * (reward_per_act - charlie_paid_reward)) // precision
        slow_calc_act = (amount * (slow_per_act - charlie_paid_slow)) // precision

        assert reward_token.balanceOf(charlie) - reward_init_bal == reward_calc_act
        assert slow_token.balanceOf(charlie) - slow_init_bal == slow_calc_act


# A user that has withdrawn should still be able to claim their rewards
def test_withdrawn_user_can_claim(multi, slow_token, mvault, alice, charlie, issue_slow_token, chain):
    amount = mvault.balanceOf(charlie)
    reward_init_bal = slow_token.balanceOf(charlie)
    mvault.approve(multi, amount, {"from": charlie})
    multi.stake(amount, charlie, {"from": charlie})

    # Confirm charlie staked
    assert mvault.balanceOf(charlie) == 0
    assert multi.userData(charlie)["tokenAmount"] == amount

    charlie_staking_token_balance_initial = mvault.balanceOf(charlie)

    chain.mine(timedelta=60)
    multi.unstake(amount, {"from": charlie})

    charlie_staking_token_balance_final = mvault.balanceOf(charlie)

    assert charlie_staking_token_balance_final == charlie_staking_token_balance_initial + amount

    precision = 10 ** 50

    (rewardTokens, rewardAmounts) = multi.claimableRewards(charlie)

    # Confirm Charlie withdrew as expected
    reward_per_token = multi.rewardData(slow_token)["rewardPerToken"]
    earned_calc = reward_per_token * amount // precision
    assert multi.userData(charlie)["tokenAmount"] == 0
    assert reward_per_token > 0
    assert earned_calc == rewardAmounts[0]

    # Does Charlie still get rewarded?
    tx = multi.getReward(charlie, [slow_token], {"from": charlie})
    for e in tx.events["RewardPaid"]:
        if e["user"] == charlie and e["rewardToken"] == slow_token:
            token_log = e
    assert token_log["reward"] == earned_calc
    assert slow_token.balanceOf(charlie) - reward_init_bal == earned_calc
