from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.providers.common.sql.sensors.sql import SqlSensor
from airflow.utils.task_group import TaskGroup
from datetime import datetime, timedelta

default_args = {
    'owner': 'tambui',
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

DBT_CMD = "cd /app/analytics/dbt && dbt run --profiles-dir . --select"

with DAG(
    'price_ingestion_pipeline_v2',
    default_args=default_args,
    description='Pipeline with EOF Marker synchronization',
    schedule_interval='*/15 * * * *',
    start_date=datetime(2026, 3, 19),
    catchup=False,
) as dag:

    batch_id = "price_{{ ts_nodash }}"

    # ── 1. Thu thập dữ liệu ──────────────────────────────────────────────────
    import os
    run_scraper = BashOperator(
        task_id='run_price_scraper',
        bash_command=f'PYTHONPATH=/app BATCH_ID={batch_id} python3 /app/src/producers/scrapers/price_producer.py',
        env={**os.environ}
    )

    # ── 2. Đợi Consumer ghi EOF vào Postgres ─────────────────────────────────
    wait_for_data = SqlSensor(
        task_id='wait_for_consumer_eof',
        conn_id='postgres_default',
        sql=f"SELECT 1 FROM raw.batch_control WHERE batch_id = '{batch_id}' AND status = 'DONE';",
        poke_interval=10,
        timeout=300,
        mode='poke'
    )

    # ── 3. dbt Transformations (TaskGroup lồng nhau) ──────────────────────────
    with TaskGroup(group_id='dbt') as dbt_group:

        with TaskGroup(group_id='staging') as staging_group:
            dbt_stg_price_data = BashOperator(
                task_id='stg_price_data',
                bash_command=f'{DBT_CMD} stg_price_data',
            )

        with TaskGroup(group_id='dimensions') as dims_group:
            dbt_dim_product = BashOperator(
                task_id='dim_product',
                bash_command=f'{DBT_CMD} dim_product',
            )
            dbt_dim_date = BashOperator(
                task_id='dim_date',
                bash_command=f'{DBT_CMD} dim_date',
            )
            dbt_dim_time = BashOperator(
                task_id='dim_time',
                bash_command=f'{DBT_CMD} dim_time',
            )

        with TaskGroup(group_id='facts') as facts_group:
            dbt_fact_price_snapshots = BashOperator(
                task_id='fact_price_snapshots',
                bash_command=f'{DBT_CMD} fact_price_snapshots',
            )

        with TaskGroup(group_id='reporting') as reporting_group:
            dbt_rpt_daily_deals = BashOperator(
                task_id='rpt_daily_deals',
                bash_command=f'{DBT_CMD} rpt_daily_deals',
            )

        # Phụ thuộc THEO THỨ TỰ: staging --> dimensions --> facts --> reporting
        staging_group >> dims_group >> facts_group >> reporting_group

    # Dependency tổng thể của DAG
    run_scraper >> wait_for_data >> dbt_group
