-- capability-network 数据库 schema（权威定义，后续不得擅自改名）
-- PostgreSQL 15+ with pgvector extension

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- ---------------------------------------------------------------------------
-- users
-- ---------------------------------------------------------------------------
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email           VARCHAR(255) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    display_name    VARCHAR(100) NOT NULL,
    avatar_url      VARCHAR(512),
    role            VARCHAR(32)  NOT NULL DEFAULT 'user',   -- user | admin
    status          VARCHAR(32)  NOT NULL DEFAULT 'active', -- active | suspended | deleted
    phone           VARCHAR(20)  UNIQUE,
    kyc_level       VARCHAR(8)   NOT NULL DEFAULT 'L0',
    kyc_real_name   VARCHAR(100),
    kyc_id_number   VARCHAR(512),
    kyc_id_number_hash VARCHAR(64) UNIQUE,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users (email);
CREATE INDEX idx_users_status ON users (status);
CREATE INDEX idx_users_phone  ON users (phone);

-- ---------------------------------------------------------------------------
-- offers（能力供给）
-- ---------------------------------------------------------------------------
CREATE TABLE offers (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID         NOT NULL REFERENCES users (id),
    title           VARCHAR(200) NOT NULL,
    description     TEXT         NOT NULL,
    category        VARCHAR(64)  NOT NULL,
    tags            JSONB        NOT NULL DEFAULT '[]',
    price_cents     BIGINT       NOT NULL CHECK (price_cents >= 0),
    currency        VARCHAR(3)   NOT NULL DEFAULT 'CNY',
    embedding       vector(1536),                          -- 语义匹配向量
    status          VARCHAR(32)  NOT NULL DEFAULT 'draft', -- draft | published | paused
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_offers_user_id   ON offers (user_id);
CREATE INDEX idx_offers_status    ON offers (status);
CREATE INDEX idx_offers_category  ON offers (category);
CREATE INDEX idx_offers_embedding ON offers USING ivfflat (embedding vector_cosine_ops);

-- ---------------------------------------------------------------------------
-- intents（能力需求）
-- ---------------------------------------------------------------------------
CREATE TABLE intents (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID         NOT NULL REFERENCES users (id),
    title           VARCHAR(200) NOT NULL,
    description     TEXT         NOT NULL,
    category        VARCHAR(64)  NOT NULL,
    tags            JSONB        NOT NULL DEFAULT '[]',
    budget_cents    BIGINT       NOT NULL CHECK (budget_cents >= 0),
    currency        VARCHAR(3)   NOT NULL DEFAULT 'CNY',
    embedding       vector(1536),
    status          VARCHAR(32)  NOT NULL DEFAULT 'open',  -- open | matching | matched | closed
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_intents_user_id   ON intents (user_id);
CREATE INDEX idx_intents_status    ON intents (status);
CREATE INDEX idx_intents_category  ON intents (category);
CREATE INDEX idx_intents_embedding ON intents USING ivfflat (embedding vector_cosine_ops);

-- ---------------------------------------------------------------------------
-- deals（交易）
-- ---------------------------------------------------------------------------
CREATE TABLE deals (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    offer_id        UUID         NOT NULL REFERENCES offers (id),
    intent_id       UUID         NOT NULL REFERENCES intents (id),
    buyer_id        UUID         NOT NULL REFERENCES users (id),
    seller_id       UUID         NOT NULL REFERENCES users (id),
    amount_cents    BIGINT       NOT NULL CHECK (amount_cents > 0),
    currency        VARCHAR(3)   NOT NULL DEFAULT 'CNY',
    status          VARCHAR(32)  NOT NULL DEFAULT 'pending', -- 见 deal-state-machine.md
    dispute_reason  TEXT,
    refund_amount_cents BIGINT   CHECK (refund_amount_cents IS NULL OR refund_amount_cents >= 0),
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    completed_at    TIMESTAMPTZ
);

CREATE INDEX idx_deals_offer_id  ON deals (offer_id);
CREATE INDEX idx_deals_intent_id ON deals (intent_id);
CREATE INDEX idx_deals_buyer_id  ON deals (buyer_id);
CREATE INDEX idx_deals_seller_id ON deals (seller_id);
CREATE INDEX idx_deals_status    ON deals (status);

-- ---------------------------------------------------------------------------
-- wallets
-- ---------------------------------------------------------------------------
CREATE TABLE wallets (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID         NOT NULL UNIQUE REFERENCES users (id),
    balance_cents   BIGINT       NOT NULL DEFAULT 0 CHECK (balance_cents >= 0),
    frozen_cents    BIGINT       NOT NULL DEFAULT 0 CHECK (frozen_cents >= 0),
    currency        VARCHAR(3)   NOT NULL DEFAULT 'CNY',
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_wallets_user_id ON wallets (user_id);

-- ---------------------------------------------------------------------------
-- wallet_ledger（钱包流水）
-- ---------------------------------------------------------------------------
CREATE TABLE wallet_ledger (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    wallet_id       UUID         NOT NULL REFERENCES wallets (id),
    deal_id         UUID         REFERENCES deals (id),
    entry_type      VARCHAR(32)  NOT NULL,  -- deposit | withdraw | freeze | unfreeze | payment | refund | fee
    amount_cents    BIGINT       NOT NULL,  -- 正数入账，负数出账
    balance_after   BIGINT       NOT NULL,
    description     VARCHAR(512),
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_wallet_ledger_wallet_id ON wallet_ledger (wallet_id);
CREATE INDEX idx_wallet_ledger_deal_id   ON wallet_ledger (deal_id);
CREATE INDEX idx_wallet_ledger_entry_type ON wallet_ledger (entry_type);

-- ---------------------------------------------------------------------------
-- match_logs（匹配记录）
-- ---------------------------------------------------------------------------
CREATE TABLE match_logs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    intent_id       UUID         NOT NULL REFERENCES intents (id),
    offer_id        UUID         NOT NULL REFERENCES offers (id),
    score           NUMERIC(5,4) NOT NULL CHECK (score >= 0 AND score <= 1),
    rank            INT          NOT NULL CHECK (rank > 0),
    algorithm       VARCHAR(64)  NOT NULL DEFAULT 'cosine_v1',
    metadata        JSONB        NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_match_logs_intent_id ON match_logs (intent_id);
CREATE INDEX idx_match_logs_offer_id  ON match_logs (offer_id);
CREATE INDEX idx_match_logs_created_at ON match_logs (created_at);

-- ---------------------------------------------------------------------------
-- deal_extensions（交易扩展字段，与 deals 表分离）
-- ---------------------------------------------------------------------------
CREATE TABLE deal_extensions (
    deal_id                  UUID PRIMARY KEY REFERENCES deals (id),
    match_log_id             UUID REFERENCES match_logs (id),
    auto_confirm             BOOLEAN      NOT NULL DEFAULT FALSE,
    auto_confirm_deadline    TIMESTAMPTZ,
    delivery_payload_url     VARCHAR(512),
    delivery_text            TEXT,
    disputed_by_id           UUID REFERENCES users (id),
    negotiated_refund        BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at               TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at               TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_deal_extensions_match_log_id ON deal_extensions (match_log_id);

-- ---------------------------------------------------------------------------
-- deal_idempotency（交易写操作幂等）
-- ---------------------------------------------------------------------------
CREATE TABLE deal_idempotency (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    idempotency_key VARCHAR(128) NOT NULL,
    operation       VARCHAR(32)  NOT NULL,
    deal_id         UUID REFERENCES deals (id),
    actor_id        UUID         NOT NULL REFERENCES users (id),
    response_json   TEXT         NOT NULL,
    expires_at      TIMESTAMPTZ  NOT NULL,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_deal_idempotency UNIQUE (idempotency_key, operation, deal_id)
);

CREATE INDEX idx_deal_idempotency_expires_at ON deal_idempotency (expires_at);

-- ---------------------------------------------------------------------------
-- refresh_tokens
-- ---------------------------------------------------------------------------
CREATE TABLE refresh_tokens (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID         NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    token_hash      VARCHAR(255) NOT NULL UNIQUE,
    expires_at      TIMESTAMPTZ  NOT NULL,
    revoked_at      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_refresh_tokens_user_id ON refresh_tokens (user_id);

-- ---------------------------------------------------------------------------
-- api_keys
-- ---------------------------------------------------------------------------
CREATE TABLE api_keys (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id           UUID         NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    platform_user_id  VARCHAR(128) NOT NULL,
    key_hash          VARCHAR(255) NOT NULL,
    key_prefix        VARCHAR(16)  NOT NULL,
    name              VARCHAR(100),
    status            VARCHAR(32)  NOT NULL DEFAULT 'active',
    created_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    rotated_at        TIMESTAMPTZ,
    expires_at        TIMESTAMPTZ
);

CREATE INDEX idx_api_keys_user_id          ON api_keys (user_id);
CREATE INDEX idx_api_keys_key_hash         ON api_keys (key_hash);
CREATE INDEX idx_api_keys_platform_user_id ON api_keys (platform_user_id);

-- ---------------------------------------------------------------------------
-- auctions (Agent 需求竞价室 Phase A)
-- ---------------------------------------------------------------------------
CREATE TABLE auctions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    intent_id       UUID         NOT NULL UNIQUE REFERENCES intents (id),
    status          VARCHAR(32)  NOT NULL DEFAULT 'open',
    selected_bid_id UUID,
    deal_id         UUID         REFERENCES deals (id),
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE auction_participants (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    auction_id   UUID NOT NULL REFERENCES auctions (id),
    offer_id     UUID NOT NULL REFERENCES offers (id),
    user_id      UUID NOT NULL REFERENCES users (id),
    match_log_id UUID REFERENCES match_logs (id),
    joined_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_auction_participant_offer UNIQUE (auction_id, offer_id)
);

CREATE INDEX idx_auction_participants_auction_id ON auction_participants (auction_id);

CREATE TABLE auction_bids (
    id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    auction_id     UUID   NOT NULL REFERENCES auctions (id),
    participant_id UUID   NOT NULL REFERENCES auction_participants (id),
    offer_id       UUID   NOT NULL REFERENCES offers (id),
    user_id        UUID   NOT NULL REFERENCES users (id),
    amount_cents   BIGINT NOT NULL,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_auction_bids_auction_id ON auction_bids (auction_id, created_at DESC);

-- Phase B 聊天介绍预留
CREATE TABLE auction_messages (
    id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    auction_id UUID NOT NULL REFERENCES auctions (id),
    user_id    UUID NOT NULL REFERENCES users (id),
    message    TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
