import logging


ENV_VARS = {
    'ENV',
    'HOST_TYPE',
    'DEPLOYMENT_CONFIG',
    'DEPLOYMENT_BRANCH',
    'CONTAINER_TYPE',
    'SERVICE',
}
LOG_LEVELS = {
    logging.WARN: ['websockets.protocol', 'websockets.server', 'uvicorn.error', 'pika', 'PIL'],
    logging.INFO: [
        's3transfer.tasks',
        's3transfer.utils',
        's3transfer.futures',
        'aioredis',
        'asyncio',
        'faker.factory',
        'factory.generate',
    ],
}

OTEL = {
    'VECTOR': ('vector', 9998),
}
