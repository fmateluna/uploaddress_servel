-- SQLBook: Code
INSERT INTO address ({columns}, last_update) 
VALUES ({values_placeholders},  CURRENT_TIMESTAMP) 
RETURNING id;