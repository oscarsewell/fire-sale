# Hardware Hound Database

PostgreSQL database for tracking product prices and user notifications.

## Schema Overview

**Core Tables:**
- `users` — User accounts with email and Discord integration
- `products` — Product URLs scraped from retail sites
- `tracked_products` — User-product associations with target/original prices
- `price_history` — Price snapshots over time for each product
- `site_names` — Retail site names (overclockers, ebuyer, awd-it)

**Auth & Verification:**
- `passwords` — Bcrypt hashes with salt
- `email_verification_tokens` — Token-based email verification
- `discord_link_codes` — Discord account linking codes

## Setup

### Initialise Schema

```bash
psql -h <RDS_ENDPOINT> -U postgres -d fire_sale < schema.sql
```

**Note:** RDS credentials are stored in AWS Secrets Manager. Lambda functions retrieve them automatically.

## Key Relationships

- `users` ← (1:N) → `tracked_products` (user watches products)
- `products` ← (1:N) → `price_history` (price snapshots)
- `tracked_products` ← (N:1) → `products` (links user to product)
- `site_names` ← (1:N) → `products` (products belong to sites)

## Data Flow

1. **Scraping** → Insert products into `products` table
2. **Price Updates** → Insert prices into `price_history`
3. **Tracking** → User creates `tracked_products` entries with target price
4. **Notifications** → Query products where current_price ≤ target_price

## Indexes

Performance indexes on:
- `tracked_products(user_id, product_id)` — Fast user queries
- `price_history(product_id, scraped_at DESC)` — Latest price lookup
- `email_verification_tokens(token)` — Token verification
- `discord_link_codes(user_id)` — Discord linking

