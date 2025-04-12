create database url_shortener;

create table users(
    id serial primary key,
    username VARCHAR(50) NOT NULL UNIQUE,
    password TEXT NOT NULL,
    avatar TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)

create table tiny_url(
    id BIGSERIAL primary key,
    user_id integer NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    url_code VARCHAR(8) CHECK (char_length(url_code) >= 3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)

create table ticketing(
    id BIGSERIAL primary key,
    range_start  BIGINT NOT NULL,
    range_end  BIGINT NOT NULL,
    current BIGINT NOT NULL CHECK (current >= range_start  and current <= range_end )
)

create index url_code_idx on tiny_url(url_code);

