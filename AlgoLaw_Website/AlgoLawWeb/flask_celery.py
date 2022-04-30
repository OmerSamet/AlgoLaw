from celery import Celery


def make_celery(app):
    celery = Celery(
        app.import_name,
        # backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
    celery.conf.update(app.config)
    celery.conf.worker_cancel_long_running_tasks_on_connection_loss = True
    celery.conf.result_backend = app.config['CELERY_RESULT_BACKEND']
    celery.conf.broker_pool_limit = None
    celery.conf.broker_connection_timeout = 1500
    # CELERY_BROKER_CONNECTION_RETRY = True
    # CELERY_BROKER_CONNECTION_MAX_RETRIES = None
    # CELERY_TASK_RESULT_EXPIRES = 60

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery
