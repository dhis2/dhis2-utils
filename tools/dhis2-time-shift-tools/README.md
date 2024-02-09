# DHIS2 Database Time Shift Utilities  (Work in Progress!)

This guide outlines the steps required to keep the demo/test database current.

**Features**:

- Ensure data isn't projected into the future.
- Ensure data remains recent.
- The script can be run periodically to update data.
- The script can be applied to any DB post data import.

To initialize the tools, load the functions into PostgreSQL using the following command:

```
psql -d <dhis2_db> -a -f dhis2_timeshift_functions.sql 
```

------

## Shifting Data Between Years

##### **Consider moving data at the start of each year.**

- To move data forward, use the function `dhis2_timeshift_one_year_forward()`. This function shifts all data, including Aggregate and Tracker/Event data in the DHIS2 database, forward by one year, adjusting dates to align periods correctly.

    **Execution**:

```sql
    select dhis2_timeshift_one_year_forward();  
```

To exclude events (which can be time-consuming):

```sql
    select dhis2_timeshift_one_year_forward_no_events();  
```

If you need to reverse the "move forward" operation:

- Use the function `dhis2_timeshift_one_year_backward()` to shift all data, including Aggregate and Tracker/Event data in the DHIS2 database, backward by one year, adjusting dates to align periods correctly.

    **Execution**:

```sql
    select dhis2_timeshift_one_year_backward();
```

To exclude events:

```sql
    select dhis2_timeshift_one_year_backward_no_events();
```


## Buffering Future Data

Buffering periods will retain the same **periodId** for the upcoming/current year but will append an extra two digits from the buffering year.

> **Example**
>
> Future year: 2022
> Buffering year: 2010
> PeriodId for a month like October 2022: `6171618`
> The new buffering periodId for October 2010 will be: `617161810`


### Shift all future data to the buffer period

    The following SQL command updates all data values by replacing the future year's periodId with the buffering year's periodId:

    ```sql
    select dhis2_timeshift_buffer_future_periods();
    ```

### Shift data from the buffering year to the current period

    Use the function `dhis2_timeshift_buffer_to_current(period_type text)` in cron jobs for each period type to shift data from the buffering year/period to the current year/period.  
    For instance, to shift monthly data:

    ```sql
    select dhis2_timeshift_buffer_to_current('monthly');
    ```

## Automating Data Shifts with Cron

Below is an example of how to ensure your data is updated periodically by setting up a cron job. This assumes your system already contains data up to the current date. If not, you'll need to use the previously mentioned functions to shift it to cover past dates up to today.

First, edit the crontab for the `postgres` user (who has DB access). Execute the following as a superuser:

```shell
sudo crontab -e -u postgres
```

Append these lines:

```shell
15 0 * * * psql -d covid-19 -c "SELECT dhis2_timeshift_buffer_to_current('Daily');" 2>&1 >/dev/null | ts >> ~/shift_dates.log
20 0 * * MON psql -d covid-19 -c "SELECT dhis2_timeshift_buffer_to_current('Weekly');" 2>&1 >/dev/null | ts >> ~/shift_dates.log
25 0 1 * * psql -d covid-19 -c "SELECT dhis2_timeshift_buffer_to_current('Monthly');" 2>&1 >/dev/null | ts >> ~/shift_dates.log
30 0 1 */3 * psql -d covid-19 -c "SELECT dhis2_timeshift_buffer_to_current('Quarterly');" 2>&1 >/dev/null | ts >> ~/shift_dates.log
```

After modifying your crontab, save and restart the service to apply the changes:

```shell
sudo systemctl restart cron
```

**Note**: The `ts` command adds a timestamp to the log. It can be installed with `sudo apt install moreutils`, but its use is optional. The `2>&1 >/dev/null` ensures only errors are logged in `shift_dates.log`, which is saved in the home directory of the `postgres` user.
