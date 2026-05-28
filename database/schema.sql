-- ENUM type for notification destinations
CREATE TYPE notification_type AS ENUM ('email', 'discord');

CREATE TABLE tracked_products (
  id SERIAL PRIMARY KEY,
  product_url VARCHAR(2048) NOT NULL,
  target_price INT NOT NULL,
  currency VARCHAR(3) NOT NULL,
  notification_destination notification_type NOT NULL,
  user_to_notify VARCHAR(255) NOT NULL,
  user_notified BOOLEAN DEFAULT FALSE NOT NULL,
  price_notified_of INT,
  FOREIGN KEY (product_url) REFERENCES price_history(product_url) ON DELETE CASCADE
);

CREATE TABLE price_history (
  product_url VARCHAR(2048) UNIQUE NOT NULL PRIMARY KEY,
  current_price INT NOT NULL,
  original_price INT NOT NULL,
  scraped_at TIMESTAMP NOT NULL,
  site_name VARCHAR(255) NOT NULL,
  currency VARCHAR(3) NOT NULL
);

CREATE INDEX idx_tracked_products_url ON tracked_products(product_url);
CREATE INDEX idx_tracked_products_user_notified ON tracked_products(user_notified);
CREATE INDEX idx_tracked_products_user ON tracked_products(user_to_notify);
CREATE INDEX idx_price_history_url_scraped ON price_history(product_url, scraped_at DESC);
CREATE INDEX idx_price_history_site ON price_history(site_name);
