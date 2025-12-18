DO $$
BEGIN
    IF NOT EXISTS (
        SELECT FROM pg_catalog.pg_roles WHERE rolname = 'qazaq_user'
    ) THEN
        CREATE ROLE qazaq_user LOGIN PASSWORD 'qazaq_pass';
    END IF;
END;
$$;

ALTER ROLE qazaq_user WITH SUPERUSER;





