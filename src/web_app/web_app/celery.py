from __future__ import absolute_import
from kombu import Exchange, Queue
import os
from celery import Celery

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web_app.settings')

from django.conf import settings  # noqa

app = Celery('web_app')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings', namespace='CELERY')


# Define queue settings 
default_exchange = Exchange('default', type='direct')
app.conf.task_queues = (
    Queue('default', default_exchange, routing_key='default'),
    Queue('mine', default_exchange, routing_key='default'),
    Queue('visualize', default_exchange, routing_key='default'),
    Queue('update', default_exchange, routing_key='default')
)
app.conf.task_default_queue = 'default'
app.conf.task_default_exchange = 'default'
app.conf.task_default_routing_key = 'default'

app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))