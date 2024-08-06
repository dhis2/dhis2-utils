-- These are the SQL commands to create the trigger function and trigger for resetting the 'admin'
-- user password hash to the original value when a user attempts to change it
-- This is used for the play instances of SL demo DB and is designed to apply only to the 'instance-manager' environment.


CREATE OR REPLACE FUNCTION reset_admin_user_password()
RETURNS TRIGGER AS $$
DECLARE
    admin_user TEXT := 'admin';
    original_password_hash TEXT := '$2a$10$wjLPViry3bkYEcjwGRqnYO1bT2Kl.ZY0kO.fwFDfMX53hitfx5.3C';
    current_env TEXT;
BEGIN
    -- Fetch the current environment setting
    current_env := current_setting('dhis2.environment', true);

    -- Only execute the reset logic if in the specified environment (e.g., 'instance-manager')
    IF current_env = 'instance-manager' THEN
        -- Check if the username is 'admin' and password hash is being changed
        IF NEW.username = admin_user AND NEW.password IS DISTINCT FROM original_password_hash THEN
            -- Reset the password hash to the original
            NEW.password := original_password_hash;
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER check_admin_user_password
BEFORE UPDATE ON userinfo
FOR EACH ROW
EXECUTE FUNCTION reset_admin_user_password();
