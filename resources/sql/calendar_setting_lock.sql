-- These are the SQL commands to create the trigger function and trigger for resetting
-- the calendar setting to 'iso8601' when a user attempts to change it.
-- This is used for the play instances of SL demo DB and is designed to apply only to the 'instance-manager' environment.

CREATE OR REPLACE FUNCTION reset_calendar_setting()
RETURNS TRIGGER AS $$
DECLARE
    calendar_setting_name TEXT := 'keyCalendar';
    default_calendar TEXT := 'iso8601';
    current_env TEXT;
BEGIN
    -- Fetch the current environment setting
    current_env := current_setting('dhis2.environment', true);

    -- Only execute the reset logic if in the specified environment
    IF current_env = 'instance-manager' THEN
        -- Check if the setting name is 'keyCalendar' and value is being changed
        IF NEW.name = calendar_setting_name AND NEW.value IS DISTINCT FROM default_calendar THEN
            -- Reset the value to iso8601
            NEW.value := default_calendar;
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for systemsetting table
CREATE TRIGGER check_calendar_setting
BEFORE UPDATE OR INSERT ON systemsetting
FOR EACH ROW
EXECUTE FUNCTION reset_calendar_setting(); 