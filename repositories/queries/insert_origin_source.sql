-- SQLBook: Code
INSERT INTO origin_source (file_name, load_time) VALUES (%s, %s) RETURNING id;
