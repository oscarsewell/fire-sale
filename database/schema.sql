DROP TABLE IF EXISTS price_history;
DROP TABLE IF EXISTS tracked_products;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS users;
DROP TYPE IF EXISTS notification_type;

-- ENUM type for notification destinations
CREATE TYPE notification_type AS ENUM ('email', 'discord');

CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  notification_destination notification_type NOT NULL,
  user_contact VARCHAR(255) NOT NULL UNIQUE            -- email or discord handle (depending on notification_destination)
);

CREATE TABLE products (
  id SERIAL PRIMARY KEY,
  product_url VARCHAR(2048) NOT NULL UNIQUE,
  site_name VARCHAR(255) NOT NULL,
  currency VARCHAR(3) NOT NULL
);

CREATE TABLE tracked_products (
  id SERIAL PRIMARY KEY,
  user_id INT NOT NULL,
  product_id INT NOT NULL,
  target_discount INT NOT NULL,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
  CONSTRAINT unique_user_product UNIQUE (user_id, product_id) -- prevents duplicate tracking
);

CREATE TABLE price_history (
  id SERIAL PRIMARY KEY,
  product_id INT NOT NULL,
  current_price INT NOT NULL,
  original_price INT NOT NULL,
  scraped_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

CREATE INDEX idx_tracked_products_user ON tracked_products(user_id);
CREATE INDEX idx_tracked_products_product ON tracked_products(product_id);
CREATE INDEX idx_price_history_product_scraped ON price_history(product_id, scraped_at DESC);
