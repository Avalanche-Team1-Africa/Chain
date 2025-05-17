// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "./HakiToken.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/Counters.sol";

/**
 * @title HakiEscrow
 * @dev Escrow contract for milestone-based payments to lawyers
 */
contract HakiEscrow is AccessControl {
    using Counters for Counters.Counter;
    
    HakiToken public hakiToken;
    
    bytes32 public constant NGO_ROLE = keccak256("NGO_ROLE");
    bytes32 public constant VERIFIER_ROLE = keccak256("VERIFIER_ROLE");
    
    Counters.Counter private _caseIdCounter;
    
    enum MilestoneStatus { Pending, Completed, Paid }
    
    struct Milestone {
        string description;
        uint256 amount;
        MilestoneStatus status;
    }
    
    struct Case {
        uint256 caseId;
        address lawyer;
        address ngo;
        uint256 totalAmount;
        uint256 releasedAmount;
        bool isActive;
        uint256[] milestoneIds;
    }
    
    mapping(uint256 => Case) public cases;
    mapping(uint256 => Milestone) public milestones;
    Counters.Counter private _milestoneIdCounter;
    
    // Events
    event CaseCreated(uint256 indexed caseId, address indexed lawyer, address indexed ngo);
    event MilestoneAdded(uint256 indexed caseId, uint256 indexed milestoneId, string description, uint256 amount);
    event MilestoneCompleted(uint256 indexed caseId, uint256 indexed milestoneId);
    event MilestonePaid(uint256 indexed caseId, uint256 indexed milestoneId, address lawyer, uint256 amount);
    
    /**
     * @dev Constructor
     * @param _hakiToken The HakiToken contract address
     */
    constructor(address _hakiToken) {
        hakiToken = HakiToken(_hakiToken);
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
    }
    
    /**
     * @dev Create a new case with escrow
     * @param lawyer Address of the lawyer to be paid
     * @return caseId The ID of the newly created case
     */
    function createCase(address lawyer) external onlyRole(NGO_ROLE) returns (uint256) {
        uint256 caseId = _caseIdCounter.current();
        _caseIdCounter.increment();
        
        cases[caseId] = Case({
            caseId: caseId,
            lawyer: lawyer,
            ngo: msg.sender,
            totalAmount: 0,
            releasedAmount: 0,
            isActive: true,
            milestoneIds: new uint256[](0)
        });
        
        emit CaseCreated(caseId, lawyer, msg.sender);
        return caseId;
    }
    
    /**
     * @dev Add a milestone to a case
     * @param caseId The ID of the case
     * @param description Description of the milestone
     * @param amount Amount of tokens to be paid for this milestone
     */
    function addMilestone(uint256 caseId, string calldata description, uint256 amount) 
        external 
        onlyNGOOrAdmin(caseId) 
    {
        require(cases[caseId].isActive, "Case is not active");
        
        uint256 milestoneId = _milestoneIdCounter.current();
        _milestoneIdCounter.increment();
        
        milestones[milestoneId] = Milestone({
            description: description,
            amount: amount,
            status: MilestoneStatus.Pending
        });
        
        cases[caseId].milestoneIds.push(milestoneId);
        cases[caseId].totalAmount += amount;
        
        emit MilestoneAdded(caseId, milestoneId, description, amount);
    }
    
    /**
     * @dev Verify completion of a milestone
     * @param caseId The ID of the case
     * @param milestoneId The ID of the milestone
     */
    function completeMilestone(uint256 caseId, uint256 milestoneId) 
        external 
        onlyRole(VERIFIER_ROLE) 
    {
        require(cases[caseId].isActive, "Case is not active");
        
        bool found = false;
        for (uint i = 0; i < cases[caseId].milestoneIds.length; i++) {
            if (cases[caseId].milestoneIds[i] == milestoneId) {
                found = true;
                break;
            }
        }
        require(found, "Milestone not found in this case");
        
        Milestone storage milestone = milestones[milestoneId];
        require(milestone.status == MilestoneStatus.Pending, "Milestone not in pending status");
        
        milestone.status = MilestoneStatus.Completed;
        
        emit MilestoneCompleted(caseId, milestoneId);
    }
    
    /**
     * @dev Release payment for a completed milestone
     * @param caseId The ID of the case
     * @param milestoneId The ID of the milestone
     */
    function releaseMilestonePayment(uint256 caseId, uint256 milestoneId) 
        external 
        onlyNGOOrAdmin(caseId) 
    {
        require(cases[caseId].isActive, "Case is not active");
        
        Case storage currentCase = cases[caseId];
        Milestone storage milestone = milestones[milestoneId];
        
        require(milestone.status == MilestoneStatus.Completed, "Milestone not completed");
        
        milestone.status = MilestoneStatus.Paid;
        currentCase.releasedAmount += milestone.amount;
        
        // Transfer tokens from contract to lawyer
        // In production, the NGO would need to approve this contract to spend tokens
        hakiToken.mint(currentCase.lawyer, milestone.amount);
        
        emit MilestonePaid(caseId, milestoneId, currentCase.lawyer, milestone.amount);
    }
    
    /**
     * @dev Get all milestone IDs for a case
     * @param caseId The ID of the case
     * @return Array of milestone IDs
     */
    function getCaseMilestones(uint256 caseId) external view returns (uint256[] memory) {
        return cases[caseId].milestoneIds;
    }
    
    /**
     * @dev Get details of a milestone
     * @param milestoneId The ID of the milestone
     * @return description The milestone description
     * @return amount The milestone amount
     * @return status The milestone status
     */
    function getMilestoneDetails(uint256 milestoneId) external view returns (
        string memory description,
        uint256 amount,
        MilestoneStatus status
    ) {
        Milestone storage milestone = milestones[milestoneId];
        return (milestone.description, milestone.amount, milestone.status);
    }
    
    /**
     * @dev Close a case (mark it as inactive)
     * @param caseId The ID of the case
     */
    function closeCase(uint256 caseId) external onlyNGOOrAdmin(caseId) {
        require(cases[caseId].isActive, "Case already inactive");
        cases[caseId].isActive = false;
    }
    
    /**
     * @dev Modifier to restrict function access to the NGO that created the case or admin
     * @param caseId The ID of the case
     */
    modifier onlyNGOOrAdmin(uint256 caseId) {
        require(
            cases[caseId].ngo == msg.sender || 
            hasRole(DEFAULT_ADMIN_ROLE, msg.sender),
            "Not authorized"
        );
        _;
    }
}