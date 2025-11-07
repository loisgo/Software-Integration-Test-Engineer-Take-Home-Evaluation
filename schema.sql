/* Sales header */
CREATE TABLE sales_hdr (
    id            BIGINT       IDENTITY PRIMARY KEY,
    sale_date     DATETIME2    NOT NULL,
    total         DECIMAL(18,2) NOT NULL,
    payment_status VARCHAR(20) NULL
);

/* Sales lines */
CREATE TABLE sales_lin (
    id       BIGINT IDENTITY PRIMARY KEY,
    hdr_id   BIGINT NOT NULL REFERENCES sales_hdr(id) ON DELETE CASCADE,
    line_no  INT    NOT NULL,
    sku      VARCHAR(30) NOT NULL,
    price    DECIMAL(18,2) NOT NULL
);

CREATE INDEX IX_sales_lin_hdr ON sales_lin(hdr_id);
