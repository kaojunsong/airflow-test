import logging
import sys
import traceback
from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator

log = logging.getLogger(__name__)


class ParameterValidationException(Exception):
    reason: str

    def __init__(self, reason: str):
        self.reason = reason

def validate_parameters(**kwargs):
    conf = kwargs.get('dag_run').conf
    kwargs['ti'].xcom_push(key='conf', value=conf)
    job_identifier = conf.get('job_identifier')
    s3_connection_id = conf.get('s3_connection_id')
    if not job_identifier:
        raise ParameterValidationException(reason='job_identifier should not be empty')
    if not s3_connection_id:
        raise ParameterValidationException(reason='s3_connection_id should not be empty')


def handle_failure(context):
    exception = context.get('exception')
    log.info(exception)
    traceback.print_exc(file=sys.stdout)


DEFAULT_ARGS = {
    'owner': 'boss_admin',
    'start_date': datetime(2021, 1, 2),
    "retries": 0,
    'on_failure_callback': handle_failure
}

with DAG(
        dag_id='monitor',
        default_args=DEFAULT_ARGS,
        schedule_interval=None
) as dag:
    validate_parameters = PythonOperator(
        task_id='validate_parameters',
        python_callable=validate_parameters,
        dag=dag,
        do_xcom_push=True,
        retries=0
    )
    validate_parameters