# ER Diagram — DzCommerce

## Core Tables

### tenants
```
id              UUID    PK
name            VARCHAR(255)
slug            VARCHAR(255)    UNIQUE, INDEX
status          VARCHAR(20)     [pending|active|suspended]
trial_ends_at   TIMESTAMP
created_at      TIMESTAMP
updated_at      TIMESTAMP
```

### users
```
id              UUID    PK
tenant_id       UUID    FK → tenants.id   INDEX
email           VARCHAR(255)    UNIQUE, INDEX
password_hash   VARCHAR(255)
name            VARCHAR(255)
role            VARCHAR(20)     [owner|admin|staff]
is_active       BOOLEAN
token_version   INTEGER
created_at      TIMESTAMP
updated_at      TIMESTAMP
```

### tenant_requests
```
id              UUID    PK
company_name    VARCHAR(255)
owner_name      VARCHAR(255)
email           VARCHAR(255)
phone           VARCHAR(50)
status          VARCHAR(20)     [pending|approved|rejected]
created_at      TIMESTAMP
updated_at      TIMESTAMP
```

### tenant_settings
```
tenant_id       UUID    PK, FK → tenants.id
currency        VARCHAR(10)     DEFAULT 'DZD'
cod_enabled     BOOLEAN         DEFAULT TRUE
language        VARCHAR(10)     DEFAULT 'ar'
```

### tenant_features
```
id              UUID    PK
tenant_id       UUID    FK → tenants.id   INDEX
feature_key     VARCHAR(100)
enabled         BOOLEAN     DEFAULT FALSE
```

### subscriptions
```
id              UUID    PK
tenant_id       UUID    FK → tenants.id   UNIQUE
plan            VARCHAR(50)     [trial|starter|pro]
status          VARCHAR(20)     [active|expired]
start_date      TIMESTAMP
end_date        TIMESTAMP
```

### products
```
id              UUID    PK
tenant_id       UUID    FK → tenants.id   INDEX
name            VARCHAR(255)
price           NUMERIC(12,2)
stock           INTEGER     DEFAULT 0
sku             VARCHAR(100)
is_active       BOOLEAN     DEFAULT TRUE
created_at      TIMESTAMP
updated_at      TIMESTAMP
```

### orders
```
id              UUID    PK
tenant_id       UUID    FK → tenants.id   INDEX
user_id         UUID    FK → users.id     INDEX
status          VARCHAR(20)     [pending→confirmed→shipped→delivered→returned|cancelled]
total           NUMERIC(12,2)
created_at      TIMESTAMP
updated_at      TIMESTAMP
```

### order_items
```
id              UUID    PK
order_id        UUID    FK → orders.id      INDEX
product_id      UUID    FK → products.id
quantity        INTEGER     DEFAULT 1
unit_price      NUMERIC(12,2)
```

### payments
```
id              UUID    PK
tenant_id       UUID    FK → tenants.id   INDEX
order_id        UUID    FK → orders.id    INDEX
amount          NUMERIC(12,2)
method          VARCHAR(20)     [COD|card|wired]
status          VARCHAR(20)     [pending|collected|failed]
collected_at    TIMESTAMP
created_at      TIMESTAMP
updated_at      TIMESTAMP
```

### audit_logs
```
id              UUID    PK
tenant_id       UUID    FK → tenants.id   INDEX
user_id         UUID    FK → users.id
action          VARCHAR(100)
entity          VARCHAR(100)
entity_id       UUID
details         JSONB
created_at      TIMESTAMP
updated_at      TIMESTAMP
```

---

## Relationships

```
tenants 1──* users
tenants 1──1 tenant_settings
tenants 1──* tenant_features
tenants 1──1 subscriptions
tenants 1──* products
tenants 1──* orders
tenants 1──* payments
tenants 1──* audit_logs

users 1──* orders
orders 1──* order_items
orders 1──* payments
products 1──* order_items
```

## Order State Machine

```
pending → confirmed → shipped → delivered → returned
    ↓          ↓
 cancelled   cancelled
```
