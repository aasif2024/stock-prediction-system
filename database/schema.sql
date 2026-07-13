-- ===================================================================
-- schema.sql
-- Stock Market Price Prediction System - MySQL Database Schema
-- ===================================================================

CREATE DATABASE IF NOT EXISTS stock_prediction_db
    CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE stock_prediction_db;

-- -------------------------------------------------------------
-- USERS
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    full_name       VARCHAR(120)  NOT NULL,
    email           VARCHAR(150)  NOT NULL UNIQUE,
    password_hash   VARCHAR(255)  NOT NULL,
    created_at      DATETIME      DEFAULT CURRENT_TIMESTAMP
);

-- -------------------------------------------------------------
-- COMPANIES
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS companies (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    company_name    VARCHAR(200)  NOT NULL,
    equity_name     VARCHAR(50)   NOT NULL UNIQUE,
    sector          VARCHAR(120)  DEFAULT NULL,
    created_at      DATETIME      DEFAULT CURRENT_TIMESTAMP
);

-- -------------------------------------------------------------
-- PREDICTION HISTORY
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS prediction_history (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    user_id             INT NOT NULL,
    company_id          INT NOT NULL,
    input_open          DECIMAL(12,2) NOT NULL,
    input_high          DECIMAL(12,2) NOT NULL,
    input_low           DECIMAL(12,2) NOT NULL,
    input_close         DECIMAL(12,2) NOT NULL,
    input_traded_qty    BIGINT        NOT NULL,
    predicted_price     DECIMAL(12,2) NOT NULL,
    direction           ENUM('UP', 'DOWN') NOT NULL,
    predicted_at        DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_prediction_user
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_prediction_company
        FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

CREATE INDEX idx_prediction_user ON prediction_history(user_id);
CREATE INDEX idx_prediction_company ON prediction_history(company_id);
