import argparse
import os
import re
import sys
import yaml


parser = argparse.ArgumentParser(description='fill yaml with environment variables')
parser.add_argument('src', help='source yaml file')
parser.add_argument('dst', help='destination yaml file')


R = re.compile('%\{(.*?)\}')
P = '%{{{}}}'.format
D = os.path.dirname(__file__)


def env(s):
    for k in R.findall(s):
        try:
            s = s.replace(P(k), os.environ.get(k))
        except TypeError as e:
            print('Cannot find env variable: {}'.format(k), file=sys.stderr)
            raise e
    return s


def set_fields(dct):
    for k, v in dct.items():
        if not v and k in os.environ:
            dct[k] = os.environ[k]


def traverse(obj):
    t = type(obj)
    if t == dict:
        return {traverse(k): traverse(v) for k, v in obj.items()}
    elif t == list:
        return list(map(traverse, obj))
    elif t == str:
        return env(obj)
    return obj


def main():
    args = parser.parse_args()
    with open(args.src) as src:
        y = yaml.load(src)
    y = traverse(y)
    with open(args.dst, 'w') as dst:
        yaml.dump(y, dst)


if __name__ == '__main__':
    main()
