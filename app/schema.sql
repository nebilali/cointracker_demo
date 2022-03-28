DROP TABLE IF EXISTS accounts;
DROP TABLE IF EXISTS transactions;

CREATE TABLE accounts (
  account_id TEXT Not NULL,
  balance INTEGER NOT NULL DEFAULT 0,
  sync_block INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (account_id)
);

CREATE TABLE transactions (
  tx_id TEXT not NULL,
  account_id TEXT not NULL,
  value_change INTEGER not NULL DEFAULT 0,
  block_num INTEGER not NULL,
  PRIMARY KEY (tx_id),
  FOREIGN KEY (account_id) REFERENCES accounts (account_id)
);