-- SQLBook: Code
INSERT INTO
    input_request (
        input_type_id,
        address_id,
        attribute_name,
        attribute_value
    )
VALUES (%s, %s, %s, %s) RETURNING id