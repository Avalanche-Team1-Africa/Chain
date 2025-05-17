# HakiChain

**HakiChain** is a Django-based legal support platform integrated with Ethereum smart contracts to bridge the gap between NGOs seeking legal assistance and lawyers offering their services either pro bono or for bounties.

The platform also features blockchain-based milestone tracking and payments using the custom `HakiToken` ERC20 token, fostering transparency and accountability in the delivery of legal aid.

---

## 🚀 Overview

HakiChain empowers NGOs to post legal cases and receive assistance from lawyers. The platform supports:

* Case management
* Lawyer applications and selection
* Milestone-based tracking and updates
* Bounty funding through donations
* On-chain reward system using `HakiToken`

---

## 🛠 Key Features

### 🌍 Django-Based Platform

* **Case Management**: NGOs can post legal cases with detailed info including urgency, location, and deadlines.
* **Lawyer Matching**: Lawyers browse cases and apply with a personalized cover letter.
* **Application Workflow**: NGOs can shortlist, review, and select lawyers.
* **Milestone Tracking**: Divide cases into manageable milestones with due dates and status.
* **Progress Updates**: Ongoing documentation of case progress by involved parties.
* **Document Management**: Upload and associate legal documents with individual cases.
* **Rating & Feedback**: NGOs rate lawyers after case completion.
* **Success Stories**: Share outcomes of impactful cases.
* **Donation System**: Users can donate HakiTokens to support legal cases.

### 🧾 Case Status Flow

1. `Open`: Posted by NGO
2. `Assigned`: Lawyer selected
3. `In Progress`: Work ongoing
4. `Under Review`: Outcome under evaluation
5. `Completed`: Legal work finalized
6. `Closed`: Case archived

### ⚠️ Urgency Levels

* Low
* Medium
* High
* Critical

---

## 💰 Blockchain Integration (Hardhat + Solidity)

HakiChain includes smart contracts deployed on the Ethereum blockchain for decentralized reward and milestone tracking.

### 🔐 HakiToken (ERC20)

An ERC20 token used to reward lawyers for completing case milestones.

* Symbol: `HAKI`
* Total Supply Cap: `100 million`
* Burnable & Mintable
* Roles: `MINTER_ROLE`, `DEFAULT_ADMIN_ROLE`
* Capped token minting to enforce accountability

**Key Functions:**

* `mint()`: Mint new tokens with role verification
* `burn()`: Lawyers can burn tokens
* `totalMinted()` / `remainingSupply()`: Track token economy

### 💼 HakiEscrow

Smart contract to manage milestone-based payments using `HakiToken`.

**Roles:**

* `NGO_ROLE`: Can create and fund cases
* `VERIFIER_ROLE`: Confirms milestone completion

**Key Features:**

* Escrow-based case creation with assigned lawyers
* Add milestones to cases with bounty amounts
* Verify milestone completion
* Release payments only upon verification
* Immutable record of transactions and progress

**Workflow:**

1. NGO creates case on-chain
2. Adds milestones and funds tokens
3. Verifier confirms milestone completion
4. Payment is released in HakiTokens

---

## 🧩 Core Django Models

* `CaseCategory`: Types of legal issues
* `Case`: Tracks legal matters
* `CaseDocument`: Case-related uploads
* `CaseUpdate`: Progress logs
* `CaseMilestone`: Milestone breakdowns
* `LawyerApplication`: Lawyer submissions
* `LawyerRating`: NGO feedback on lawyers
* `SuccessStory`: Published outcomes

---

## 🔧 Getting Started

### ✅ Prerequisites

* Python 3.10+
* Django 4.x
* PostgreSQL
* Node.js + Hardhat (for smart contract deployment)

### 🐍 Backend Setup

```bash
git clone https://github.com/yourusername/hakichain.git
cd hakichain

python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# Update DB settings in hakichain/settings.py

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### ⛓️ Blockchain Setup

```bash
cd blockchain
npm install

# Compile contracts
npx hardhat compile

# Run local Ethereum node
npx hardhat node

# Deploy contracts to local network
npx hardhat run scripts/deploy.js --network localhost
```

---

## 👥 Usage

### For NGOs

* Register & log in
* Post legal cases
* Review & select lawyer applications
* Track milestones and updates
* Rate lawyers and share success stories
* Donate HakiTokens to reward efforts

### For Lawyers

* Register with your credentials
* Apply for cases with a cover letter
* Track assigned cases and milestones
* Receive HakiTokens upon milestone completion
* Build your legal portfolio with ratings and reviews

---

## 👨‍💻 Contributing

Contributions are welcome! Feel free to fork the repo and submit pull requests.

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).

---


