#!/usr/bin/env python3
import argparse
import os

from tipsi_tools.unix import succ

parser = argparse.ArgumentParser(description='ci script: build, push branches/tags, cache')
parser.add_argument('-r', '--repo', dest='repo', help='push repo')
parser.add_argument('-p', '--project', dest='project')

parser.add_argument('-t', '--tag', dest='tag', default=os.environ.get('CI_COMMIT_TAG'))
parser.add_argument('--branch-name', dest='branch', default=os.environ.get('CI_COMMIT_REF_NAME'))
parser.add_argument('--push-branches', dest='push_branches', default='master,staging')

parser.add_argument('--docker-file', dest='docker_file', default='Dockerfile')
parser.add_argument('--test', help='test command', default='true')
parser.add_argument(
    '--cache-name',
    help='image cache name',
    default='{}_cache'.format(os.environ.get('CI_PROJECT_NAME', 'default')),
)
parser.add_argument(
    '--temp-name', dest='temp_name', help='temp image name', default=os.environ.get('CI_JOB_ID')
)
args = parser.parse_args()

FULL_BRANCH = '{}/{}:{}'.format(args.repo, args.project, args.branch)
FULL_TAG = '{}/{}:{}'.format(args.repo, args.project, args.tag)


def build():
    sha = args.temp_name
    cmd = ['docker build -t', sha, '-f', args.docker_file, '.']
    print('Build: {}'.format(' '.join(cmd)))
    succ(cmd)


def run_test():
    succ([args.test], check_stderr=False)


def push_branch():
    if args.branch not in args.push_branches.split(','):
        print('Skip push branch: {}'.format(args.branch))
        return
    print('Push branch {}'.format(args.branch))
    succ(['docker tag ', args.temp_name, FULL_BRANCH])
    succ(['docker push ', FULL_BRANCH])


def push_tag():
    if not args.tag:
        print('Skip push tag')
        return
    print('Push tag: {}'.format(args.tag))
    succ(['docker tag', args.temp_name, FULL_TAG])
    succ(['docker push', FULL_TAG])


def cache():
    print('Cache image as: {}'.format(args.cache_name))
    succ(['docker tag', args.temp_name, args.cache_name, '&& docker rmi', args.temp_name])


def main():
    build()
    run_test()
    push_branch()
    push_tag()
    cache()


if __name__ == '__main__':
    main()
