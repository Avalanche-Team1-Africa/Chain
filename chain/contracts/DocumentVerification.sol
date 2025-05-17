// SPDX-License-Identifier: MIT
pragma solidity ^0.8.30;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "./HakiCounters.sol";  // Updated import

/**
 * @title DocumentVerification
 * @dev Manages storage and verification of legal document hashes on-chain
 */
contract DocumentVerification is AccessControl {
    using HakiCounters for HakiCounters.Counter;  // Updated usage
    
    // Roles
    bytes32 public constant UPLOADER_ROLE = keccak256("UPLOADER_ROLE");
    
    // Counter for document IDs
    HakiCounters.Counter private _documentIdCounter;  // Updated type
    
    // Document structure
    struct Document {
        uint256 id;
        bytes32 documentHash;
        uint256 caseId;
        address uploader;
        uint256 timestamp;
        string documentType;
        string ipfsHash;
    }
    
    // Mappings
    mapping(uint256 => Document) private documents;
    mapping(uint256 => uint256[]) private caseDocuments;
    
    // Events
    event DocumentAdded(
        uint256 indexed documentId,
        bytes32 indexed documentHash,
        uint256 indexed caseId,
        address uploader,
        string documentType,
        string ipfsHash
    );
    
    // Constructor
    constructor() {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(UPLOADER_ROLE, msg.sender);
    }
    
    /**
     * @dev Adds a new document entry
     */
    function addDocument(
        bytes32 documentHash,
        uint256 caseId,
        string calldata documentType,
        string calldata ipfsHash
    ) external onlyRole(UPLOADER_ROLE) returns (uint256) {
        uint256 documentId = _documentIdCounter.current();
        _documentIdCounter.increment();
        
        documents[documentId] = Document({
            id: documentId,
            documentHash: documentHash,
            caseId: caseId,
            uploader: msg.sender,
            timestamp: block.timestamp,
            documentType: documentType,
            ipfsHash: ipfsHash
        });
        
        caseDocuments[caseId].push(documentId);
        
        emit DocumentAdded(
            documentId,
            documentHash,
            caseId,
            msg.sender,
            documentType,
            ipfsHash
        );
        
        return documentId;
    }
    
    /**
     * @dev Verifies a document hash
     */
    function verifyDocument(uint256 documentId, bytes32 documentHash)
        external
        view
        returns (bool)
    {
        return documents[documentId].documentHash == documentHash;
    }
    
    /**
     * @dev Returns details of a specific document
     */
    function getDocument(uint256 documentId)
        external
        view
        returns (
            bytes32 documentHash,
            uint256 caseId,
            address uploader,
            uint256 timestamp,
            string memory documentType,
            string memory ipfsHash
        )
    {
        Document storage doc = documents[documentId];
        return (
            doc.documentHash,
            doc.caseId,
            doc.uploader,
            doc.timestamp,
            doc.documentType,
            doc.ipfsHash
        );
    }
    
    /**
     * @dev Returns all document IDs related to a case
     */
    function getCaseDocuments(uint256 caseId)
        external
        view
        returns (uint256[] memory)
    {
        return caseDocuments[caseId];
    }
}