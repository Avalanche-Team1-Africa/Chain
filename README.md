# HakiChain


HakiChain is a Django-based platform designed to bridge the gap between NGOs seeking legal assistance and lawyers willing to offer their services pro bono or for bounties.

## Overview

This platform enables NGOs to post legal cases requiring assistance, while lawyers can browse these cases and apply to work on them. The system facilitates case management, lawyer applications, bounty funding, and success tracking through a comprehensive workflow.

## Key Features

- **Case Management**: NGOs can post cases with detailed descriptions, urgency levels, locations, and deadlines
- **Lawyer Matching**: Lawyers can browse open cases and apply with cover letters
- **Application Process**: NGOs can shortlist, review, and select lawyers for their cases
- **Milestone Tracking**: Cases can be broken down into milestones with target dates and status tracking
- **Case Updates**: Ongoing case progress can be documented through periodic updates
- **Document Management**: Legal documents can be uploaded and associated with specific cases
- **Rating System**: NGOs can provide ratings and reviews for lawyers upon case completion
- **Success Stories**: Notable case outcomes can be published as success stories
- **Donation System**: Cases can receive bounty funding through donations

## Models

### Core Models

- **CaseCategory**: Classification system for different types of legal cases
- **Case**: The central model tracking all aspects of a legal matter
- **CaseDocument**: Legal files and documents pertaining to specific cases
- **CaseUpdate**: Progress updates posted by involved parties
- **CaseMilestone**: Key deliverables and objectives for case resolution
- **LawyerApplication**: Applications from lawyers interested in cases
- **LawyerRating**: Feedback and scores for lawyer performance
- **SuccessStory**: Highlighted successful case outcomes

### Case Status Flow

Cases progress through the following statuses:
1. **Open**: Initial state when posted by an NGO
2. **Assigned**: A lawyer has been selected and assigned
3. **In Progress**: Active work is underway
4. **Under Review**: Case outcome is being evaluated
5. **Completed**: Legal work has been successfully finished
6. **Closed**: Case has been finalized and archived

### Urgency Levels

Cases can be marked with urgency levels:
- Low
- Medium
- High
- Critical

## Getting Started

### Prerequisites

- Python 3.10+
- Django
- Database (PostgreSQL recommended)

### Installation

1. Clone the repository
2. Create and activate a virtual environment
3. Install dependencies: `pip install -r requirements.txt`
4. Configure your database in settings.py
5. Run migrations: `python manage.py migrate`
6. Create a superuser: `python manage.py createsuperuser`
7. Start the development server: `python manage.py runserver`

## Usage

### For NGOs

1. Register an NGO account
2. Create and post legal cases
3. Review lawyer applications
4. Track case progress
5. Rate lawyers upon completion

### For Lawyers

1. Register a lawyer account with relevant profile information
2. Browse available cases
3. Apply for cases with a cover letter
4. Update case progress
5. Build reputation through ratings and success stories

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the [MIT License](LICENSE).