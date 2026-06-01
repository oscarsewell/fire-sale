DROP TABLE IF EXISTS price_history;
DROP TABLE IF EXISTS tracked_products;
DROP TABLE IF EXISTS passwords;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS site_names;

CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  username VARCHAR(255) NOT NULL UNIQUE,
  email VARCHAR(255) NOT NULL UNIQUE,
  discord VARCHAR(255) UNIQUE
);

CREATE TABLE passwords (
  id SERIAL PRIMARY KEY,
  user_id INT NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  salt VARCHAR(255) NOT NULL,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE site_names (
  id SERIAL PRIMARY KEY,
  site VARCHAR(255) NOT NULL UNIQUE
);

CREATE TABLE products (
  id SERIAL PRIMARY KEY,
  product_url VARCHAR(2048) NOT NULL UNIQUE,
  product_name VARCHAR(255) NOT NULL,
  site_id INT NOT NULL,
  currency VARCHAR(3) NOT NULL,
  FOREIGN KEY (site_id) REFERENCES site_names(id) ON DELETE CASCADE
);

CREATE INDEX idx_products_site_id ON products(site_id);

CREATE TABLE tracked_products (
  id SERIAL PRIMARY KEY,
  user_id INT NOT NULL,
  product_id INT NOT NULL,
  target_price INT NOT NULL,
  original_price INT NOT NULL,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
  CONSTRAINT unique_user_product UNIQUE (user_id, product_id) -- prevents duplicate tracking
);

CREATE TABLE price_history (
  id SERIAL PRIMARY KEY,
  product_id INT NOT NULL,
  current_price INT NOT NULL,
  scraped_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

CREATE INDEX idx_tracked_products_user ON tracked_products(user_id);
CREATE INDEX idx_tracked_products_product ON tracked_products(product_id);
CREATE INDEX idx_price_history_product_scraped ON price_history(product_id, scraped_at DESC);
