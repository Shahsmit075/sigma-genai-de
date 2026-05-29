<<<<<<< HEAD
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.exceptions import AirflowFailException
import logging
import json

# Define default arguments for the DAG
=======
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import logging
import json

>>>>>>> 83d5fc253a8457c3903da527641897b01c810c15
default_args = {
    'owner': 'data-engineering',
   'retries': 2,
   'retry_delay': timedelta(minutes=5),
<<<<<<< HEAD
    'email_on_failure': True,
}

# Define the DAG
dag = DAG(
    dag_id='sigma_transaction_pipeline',
    default_args=default_args,
    schedule='0 2 * * *',
    start_date=datetime(2024, 1, 1),
    catchup=False,
    description="Daily Bronze->Silver->Gold pipeline for Sigma DataTech transactions",
    tags=['sigma', 'transactions', 'daily'],
    sla_miss_callback=lambda context: logging.warning(
        f"SLA miss for DAG {context['dag'].dag_id} at {context['execution_date']}"
    ),
    on_failure_callback=lambda context: logging.warning(
        f"Failure in DAG {context['dag'].dag_id}, task {context['task_instance'].task_id} at {context['execution_date']}: {context['exception']}"
    ),
)

def log_task_status(context):
    """Log the start and end of a task with task instance info."""
    task_instance = context['task_instance']
    logging.info(f"Task {task_instance.task_id} started at {task_instance.start_date}")
    yield
    logging.info(f"Task {task_instance.task_id} ended at {task_instance.end_date}")

def extract_bronze(**context):
    """Ingest raw CSVs to Bronze Parquet."""
    try:
        # Placeholder for actual extraction logic
        logging.info("Extracting raw CSVs to Bronze Parquet")
    except Exception as e:
        logging.error(f"Error in extract_bronze: {e}")
        raise AirflowFailException(f"extract_bronze failed: {e}")

def transform_silver(**context):
    """Clean, enrich, deduplicate to Silver."""
    try:
        # Placeholder for actual transformation logic
        logging.info("Transforming data to Silver layer")
    except Exception as e:
        logging.error(f"Error in transform_silver: {e}")
        raise AirflowFailException(f"transform_silver failed: {e}")

def build_gold(**context):
    """Generate the 3 Gold aggregation tables."""
    try:
        # Placeholder for actual aggregation logic
        logging.info("Building Gold layer aggregation tables")
    except Exception as e:
        logging.error(f"Error in build_gold: {e}")
        raise AirflowFailException(f"build_gold failed: {e}")

# Define tasks with on_failure_callback
extract_bronze_task = PythonOperator(
    task_id='extract_bronze',
    python_callable=extract_bronze,
    provide_context=True,
    on_failure_callback=log_task_status,
    dag=dag,
)

transform_silver_task = PythonOperator(
    task_id='transform_silver',
    python_callable=transform_silver,
    provide_context=True,
    on_failure_callback=log_task_status,
    dag=dag,
)

build_gold_task = PythonOperator(
    task_id='build_gold',
    python_callable=build_gold,
    provide_context=True,
    on_failure_callback=log_task_status,
    dag=dag,
)

# Define task dependencies
extract_bronze_task >> transform_silver_task >> build_gold_task
=======
    'email_on_failure': True
}

def on_failure_callback(context):
    """Logs failure details."""
    dag_id = context['dag'].dag_id
    task_id = context['task_instance'].task_id
    execution_date = context['execution_date']
    error_message = context['exception']
    logging.error(f"DAG: {dag_id}, Task: {task_id}, Execution Date: {execution_date}, Error: {error_message}")

def sla_miss_callback(context):
    """Sends alert for SLA miss."""
    dag_id = context['dag'].dag_id
    execution_date = context['execution_date']
    logging.warning(f"DAG: {dag_id}, Execution Date: {execution_date}, SLA Miss")

def extract_bronze(**context):
    """Ingest raw CSVs to Bronze Parquet."""
    logging.info("Starting extract_bronze task")
    # Add your code here
    logging.info("Ending extract_bronze task")

def transform_silver(**context):
    """Clean, enrich, deduplicate to Silver."""
    logging.info("Starting transform_silver task")
    # Add your code here
    logging.info("Ending transform_silver task")

def build_gold(**context):
    """Generate the 3 Gold aggregation tables."""
    logging.info("Starting build_gold task")
    # Add your code here
    logging.info("Ending build_gold task")

with DAG(
    dag_id='sigma_transaction_pipeline',
    schedule='0 2 * * *',
    start_date=datetime(2024, 1, 1),
    catchup=False,
    default_args=default_args,
    on_failure_callback=on_failure_callback,
    sla_miss_callback=sla_miss_callback,
    tags=['sigma', 'transactions', 'daily'],
    description="Daily Bronze->Silver->Gold pipeline for Sigma DataTech transactions"
) as dag:

    extract_bronze_task = PythonOperator(
        task_id='extract_bronze',
        python_callable=extract_bronze,
        on_failure_callback=on_failure_callback
    )

    transform_silver_task = PythonOperator(
        task_id='transform_silver',
        python_callable=transform_silver,
        on_failure_callback=on_failure_callback
    )

    build_gold_task = PythonOperator(
        task_id='build_gold',
        python_callable=build_gold,
        on_failure_callback=on_failure_callback
    )

    extract_bronze_task >> transform_silver_task >> build_gold_task
>>>>>>> 83d5fc253a8457c3903da527641897b01c810c15
