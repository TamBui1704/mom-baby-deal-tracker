{% macro cleanup_dbt_backups() %}
    {#
        Tự động dọn dẹp các relation __dbt_backup bị kẹt lại do lần chạy trước bị crash.
        Hook này chạy TRƯỚC mỗi lần `dbt run` để ngăn lỗi:
        "relation stg_xxx__dbt_backup already exists"
    #}
    {% set cleanup_sql %}
        DO $$
        DECLARE
            r RECORD;
        BEGIN
            -- Xóa tất cả VIEW có tên kết thúc bằng __dbt_backup
            FOR r IN
                SELECT table_schema, table_name
                FROM information_schema.tables
                WHERE table_name LIKE '%__dbt_backup'
                  AND table_type = 'VIEW'
            LOOP
                EXECUTE 'DROP VIEW IF EXISTS ' || quote_ident(r.table_schema) || '.' || quote_ident(r.table_name) || ' CASCADE';
                RAISE NOTICE 'Dropped backup view: %.%', r.table_schema, r.table_name;
            END LOOP;

            -- Xóa tất cả TABLE có tên kết thúc bằng __dbt_backup
            FOR r IN
                SELECT table_schema, table_name
                FROM information_schema.tables
                WHERE table_name LIKE '%__dbt_backup'
                  AND table_type = 'BASE TABLE'
            LOOP
                EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.table_schema) || '.' || quote_ident(r.table_name) || ' CASCADE';
                RAISE NOTICE 'Dropped backup table: %.%', r.table_schema, r.table_name;
            END LOOP;
        END $$;
    {% endset %}

    {% do run_query(cleanup_sql) %}
    {{ log("✅ Cleanup __dbt_backup relations hoàn tất.", info=True) }}
{% endmacro %}
