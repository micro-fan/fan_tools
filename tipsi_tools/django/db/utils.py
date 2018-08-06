def postgres_set(connection, parameter, value):
    with connection.cursor() as cursor:
        cursor.execute('SET "{}" = %s'.format(parameter), (value,))


def set_word_similarity_threshold(value):
    from django.db import connection

    postgres_set(connection, 'pg_trgm.word_similarity_threshold', value)
