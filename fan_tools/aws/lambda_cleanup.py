#!/usr/bin/env python3

import argparse
from datetime import datetime, timedelta
from typing import Optional

import boto3
import pytz
from dateutil.parser import parse


LAST_VERSIONS_COUNT = 4
MINIMUM_PERIOD_DAYS = 14


def get_alias_from_name(name: str) -> Optional[str]:
    parts = name.split(':')

    if len(parts) == 1:
        return
    return parts[-1]


def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--last-versions-count', type=int, default=LAST_VERSIONS_COUNT)
    arg_parser.add_argument('--minimum-period-days', type=int, default=MINIMUM_PERIOD_DAYS)
    arg_parser.add_argument('--dry', action='store_true')
    arg_parser.add_argument('--aws-access-key-id', required=False)
    arg_parser.add_argument('--aws-secret-access-key', required=False)
    arg_parser.add_argument('--region-name', required=False)
    arg_parser.add_argument('--function-name', required=False)
    arg_parser.add_argument('--actual-names', nargs='+', required=False, default=set())
    arg_parser.add_argument('--ecr-repo-name')

    args = arg_parser.parse_args()

    aws_kwargs = {}

    if args.aws_access_key_id is not None:
        aws_kwargs['aws_access_key_id'] = args.aws_access_key_id
    if args.aws_secret_access_key is not None:
        aws_kwargs['aws_secret_access_key'] = args.aws_secret_access_key
    if args.region_name is not None:
        aws_kwargs['region_name'] = args.region_name

    dry = args.dry

    if dry:
        print('Dry run!')

    lambda_client = boto3.client('lambda', **aws_kwargs)
    ecr_client = boto3.client('ecr', **aws_kwargs)

    actual_from = datetime.now(tz=pytz.utc) - timedelta(days=args.minimum_period_days)

    function_name = args.function_name
    actual_names = set(args.actual_names)
    repo_name = args.ecr_repo_name

    print(f'Clean for {function_name}')
    all_versions = lambda_client.list_versions_by_function(FunctionName=function_name)['Versions']
    all_versions = list(filter(lambda v: v['Version'] != '$LATEST', all_versions))
    all_versions.sort(key=lambda v: int(v['Version']), reverse=True)
    actual_aliases = set(filter(lambda k: k is not None, map(get_alias_from_name, actual_names)))
    available_aliases = {
        a['Name']: a
        for a in lambda_client.list_aliases(FunctionName=function_name)['Aliases']
    }
    actual_versions = {v['Version'] for v in all_versions[:args.last_versions_count]}
    actual_images_uri = set()

    for version_data in all_versions:
        if parse(version_data['LastModified']) >= actual_from:
            actual_versions.add(version_data['Version'])

    for alias in actual_aliases:
        actual_versions.add(available_aliases.pop(alias)['FunctionVersion'])

    for v in actual_versions:
        resp = lambda_client.get_function(FunctionName=function_name, Qualifier=v)
        if resp['Code'].get('ImageUri') is not None:
            actual_images_uri.add(resp['Code']['ImageUri'])

    unused_aliases = [
        a for a in available_aliases.values() if a['FunctionVersion'] not in actual_versions
    ]
    to_del_aliases = {a['Name'] for a in unused_aliases}
    to_del_versions = {v['Version'] for v in all_versions} - actual_versions

    for alias in to_del_aliases:
        print(f'Delete alias: {alias}')
        if not dry:
            lambda_client.delete_alias(FunctionName=function_name, Name=alias)

    to_delete_image_tags = set()

    for version in to_del_versions:
        print(f'Delete version: {version}')

        image_uri = lambda_client.get_function(
            FunctionName=function_name,
            Qualifier=version,
        )['Code'].get('ImageUri')

        if not dry:
            lambda_client.delete_function(FunctionName=function_name, Qualifier=version)

        if image_uri is not None and image_uri not in actual_images_uri:
            print(f'Delete image uri: {image_uri}')
            to_delete_image_tags.add(image_uri.split(':')[-1])

    if to_delete_image_tags:
        print(f'Delete tags {to_delete_image_tags}')
        if not dry:
            ecr_client.batch_delete_image(
                repositoryName=repo_name,
                imageIds=[{'imageTag': t} for t in to_delete_image_tags],
            )


if __name__ == '__main__':
    main()
