INSERT INTO sales_hdr(sale_date,total,payment_status)
VALUES (GETUTCDATE(), 0, 'PENDING');

INSERT INTO sales_lin(hdr_id,line_no,sku,price)
VALUES (SCOPE_IDENTITY(), 1, 'TEST‑SKU', 9.99);
