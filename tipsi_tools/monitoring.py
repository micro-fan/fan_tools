"""
Monitoring tools are here
Main goal is to provide easy to use monitoring solution.
Write monitoring strings to logs, ship them to kibana, extract/aggreate to monitoring system
"""
import logging


log_mon = logging.getLogger('monitoring')


def log_mon_value(name, value=1, **kwargs):
    """
    simplest monitoring function to be aggregated with sum
    """
    message = '{} => {}'.format(name, value)
    log_mon.info({'metric_name': name,
                  'value': value,
                  'message': message,
                  **kwargs})

