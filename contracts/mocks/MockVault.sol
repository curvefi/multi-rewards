// SPDX-License-Identifier: MIT
pragma solidity >=0.8.12;

import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";

import {IHypervisor} from "interfaces/IHypervisor.sol";

// the MockVault is the stakingToken
contract MockVault is IHypervisor, ERC20 {
    address[] public rewardTokens;
    mapping(address => bool) internal isRewardToken;
    address public farmingContract;

    constructor(uint256 initialSupply) ERC20("Gold", "GLD") {
        _mint(msg.sender, initialSupply);
    }

    function _mint_for_testing(address account, uint256 amount) external {
        _mint(account, amount);
    }

    function setFarmingContract(address _farmingContract) external {
        farmingContract = _farmingContract;
    }

    function setRewardTokens(address[] memory _rewardTokens) external {
        require(farmingContract > address(0), "NO_FM_SET");
        for (uint i; i < _rewardTokens.length; i++) {
            address rewardToken = _rewardTokens[i];
            if (!isRewardToken[rewardToken]) {
                isRewardToken[rewardToken] = true;
                rewardTokens.push(rewardToken);
            }
        }
    }

    // The mock getReward doesn't collect any rewards from a Gauge contract
    // so rewards should be transferred to MockVault accordingly
    function getReward() external {
        for (uint i; i < rewardTokens.length; i++) {
            IERC20 rewardToken = IERC20(rewardTokens[i]);
            uint256 balance = rewardToken.balanceOf(address(this));
            rewardToken.transfer(farmingContract, balance);
        }
    }
}
