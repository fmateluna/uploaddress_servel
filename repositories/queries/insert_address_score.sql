-- SQLBook: Code
INSERT INTO address_score (address_id, quality_label, score) VALUES (%s, %s, %s) RETURNING id;
