# Hardware Hound

An automated, high-frequency e-commerce sale tracking application designed to help PC builders and hardware enthusiasts get the best deals on computer parts. 

The application scans leading UK computer hardware retailers, cleans raw product pricing, checks for price drops against user-defined target prices, and delivers instant, multi-channel alerts (via Email and Discord DMs).

Supported websites:
- AWD-IT
- Ebuyer
- Overclockers

## Project Structure
The key phases of this project:
- `full_scraping/`: Full metadata extraction (original price, current price, product name, currency code) utilized for seeding newly registered URLs.
- `partial_scraping/`: Highly efficient scrappers extracting only volatile data (current price, availability) to minimize pipeline footprint.
- `cleaning/`: Sanitizss raw strings, converts major currencies into integer-mapped cents/pence, loads credentials securely, and commits cleaned updates to DB.
- `notifications/`: Compiles changes, evaluates price thresholds against target margins, marks defunct trackers, and builds notification bodies.
- `discord_bot/`: Discord client bot hosted on ECS Fargate. Delivers asynchronous user alerts and direct site tracking commands using SQS queues and RDS.
- `database/`: Defines SQL schema for user accounts, salted credentials, link codes, site names, product metadata and pricing timelines in schema.sql.
- `dashboard/`: Streamlit dashboard web application featuring custom database interactions, user-management mechanics, validation handlers, and SES confirmation emails.
- `product_checker/`: Retrieves list of active tracked products, groups them by site, and structures inputs for parallel scraping.

Other folders:
- `.github/`
- `tests/`
- `terraform/`

## Setup & Installation

Refer to README.md in each directory.

## Contributors
The team members on this project are:
- **Project Manager**: Carolina Guevara
- **Quality Assurance**: Zeinab Hussain and Tom King
- **Architect**: Oscar Sewell
- **Data Engineers & Analysts**: Everyone
