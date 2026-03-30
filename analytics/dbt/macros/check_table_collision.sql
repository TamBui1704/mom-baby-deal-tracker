
{% macro check_table_collision() %}
    {%- set schema_name = this.schema -%}
    {%- set table_name = this.table -%}
    
    {%- set check_query -%}
        SELECT count(*) 
        FROM information_schema.tables 
        WHERE table_schema = '{{ schema_name }}' 
          AND table_name = '{{ table_name }}'
          AND table_type = 'BASE TABLE'
    {%- endset -%}

    {%- set results = run_query(check_query) -%}
    
    {%- if execute -%}
        {%- set table_exists = results.columns[0].values()[0] > 0 -%}
        
        {# Nếu bảng tồn tại nhưng dbt chưa từng quản lý nó (không có trong manifest cũ hoặc không có comment của dbt) #}
        {%- if table_exists -%}
            {{ log("CẢNH BÁO: Phát hiện bảng " ~ schema_name ~ "." ~ table_name ~ " đã tồn tại. dbt có thể sẽ xóa nó.", info=True) }}
            {# Bạn có thể dùng 'exceptions.raise_compiler_error' ở đây để dừng hẳn dbt run #}
        {%- endif -%}
    {%- endif -%}
{% endmacro %}
