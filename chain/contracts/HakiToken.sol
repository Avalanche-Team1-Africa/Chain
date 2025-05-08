// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";

/**
 * @title HakiToken
 * @dev ERC20 Token for the HakiChain platform
 * Used to reward lawyers for milestone completion in cases
 */
contract HakiToken is ERC20, ERC20Burnable, AccessControl {
    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");
    
    // Maximum supply cap (100 million tokens with 18 decimals)
    uint256 public constant MAX_SUPPLY = 100_000_000 * 10**18;
    
    // Track total minted tokens
    uint256 private _totalMinted;

    /**
     * @dev Constructor that gives the deployer the admin role
     */
    constructor() ERC20("HakiToken", "HAKI") {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(MINTER_ROLE, msg.sender);
    }

    /**
     * @dev Creates `amount` new tokens and assigns them to `account`.
     * @param to The address to mint tokens to
     * @param amount The amount of tokens to mint
     */
    function mint(address to, uint256 amount) public onlyRole(MINTER_ROLE) {
        require(_totalMinted + amount <= MAX_SUPPLY, "HakiToken: Max supply exceeded");
        _totalMinted += amount;
        _mint(to, amount);
    }
    
    /**
     * @dev Returns the total amount of tokens minted
     */
    function totalMinted() public view returns (uint256) {
        return _totalMinted;
    }
    
    /**
     * @dev Returns the remaining amount of tokens that can be minted
     */
    function remainingSupply() public view returns (uint256) {
        return MAX_SUPPLY - _totalMinted;
    }
    
    // Override required by Solidity
    function supportsInterface(bytes4 interfaceId)
        public
        view
        override(AccessControl)
        returns (bool)
    {
        return super.supportsInterface(interfaceId);
    }
}