"""
Returns monitoring certificate expiration
"""
import asyncio
import logging
from datetime import datetime

from tipsi_tools.unix import asucc

log = logging.getLogger('monitoring.certs')

DAY_LOOP = 24 * 60 * 60
FMT = '%b %d %H:%M:%S %Y %Z'
CERT_CMD = (
    'echo | openssl s_client -connect {}:443 -servername {} -showcerts 2>/dev/null'  # noqa
    ' | openssl x509 -inform pem -noout -enddate'
)


CERT_HOSTS = ['gettipsi.com', 'proofnetwork.io']


async def get_certs_metrics(cert_hosts):
    metrics = {}
    for host in cert_hosts:
        cmd = CERT_CMD.format(host, host)
        log.debug(f'Run cmd: {cmd}')
        _code, stdout, stderr = await asucc(cmd)
        resp = stdout[0].split('=')[1]
        # notAfter=Dec 25 23:59:59 2018 GMT
        d = datetime.strptime(resp, FMT)
        days_remain = (d - datetime.now()).days
        log.debug(f'Certs response {host} => {days_remain} {resp}')
        metric_name = f'certificate{{config="{host}"}}'
        metrics[metric_name] = days_remain
    return metrics


async def update_certs_loop(update_metrics, hosts):
    while True:
        try:
            metrics = await get_certs_metrics(hosts)
            local_names = update_metrics(metrics)
            log.debug(f'CERTS: {metrics} => {local_names}')
            await asyncio.sleep(DAY_LOOP)
        except Exception:
            log.exception('While get certificates')
            await asyncio.sleep(10)
