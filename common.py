#!/usr/bin/python3
import sys

import argparse
import os
from typing import Generator, List
import requests

# Set a default local artifact root so that you don't have to type it on the command-line all the time
DEFAULT_LOCAL_ARTIFACT_ROOT = None

# Set a default AWS bucket URI so that you don't have to type it on the command-line all the time
DEFAULT_AWS_BUCKET_URI = None
DEFAULT_AWS_PROFILE = "Default"

# Set a default local artifact backup root so that you don't have to type it on the command-line all the time
DEFAULT_ARTIFACT_BACKUP_ROOT = None

# Set a default project; default is to look in all projects
DEFAULT_PROJECT_ROOT = "_Root"

# Set a default URL for the teamcity server
DEFAULT_TEAMCITY_URL = None
DEFAULT_TEAMCITY_USER = None
DEFAULT_TEAMCITY_PASS = None


def add_local_artifact_root_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('-l', '--local-artifact-root', default=DEFAULT_LOCAL_ARTIFACT_ROOT, required=True,
                        help='Current local artifact root with TeamCity artifacts. For example, '
                             '`/home/teamcity/.BuildServer/system/artifacts`')


def add_project_root_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('-p', '--project-root', default=DEFAULT_PROJECT_ROOT, required=True,
                        help='Top level project to search for artifacts')


def add_aws_profile_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('-a', '--aws-profile',
                        default=DEFAULT_AWS_PROFILE, required=False, help='AWS profile')


def add_aws_bucket_uri_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('-u', '--aws-bucket-uri', default=DEFAULT_AWS_BUCKET_URI, required=True,
                        help='AWS bucket URI where artifacts can be stored. Takes the form `s3://<BUCKET_NAME>`, such '
                             'as `s3://my-cool-bucket`')


def add_dry_mode_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('-d', '--dry', action='store_true',
                        help='Run in "dry" mode where no actions are actually performed, only log statements written '
                             'to the console')


def add_teamcity_feature_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('-t', '--teamcity_feature', action='store', required=True,
                        help='The TeamCity feature identifier for the S3 artifact storage backend')


def add_teamcity_user_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('-U', '--teamcity_user', action='store', required=True,
                        help='The TeamCity URL Username')


def add_teamcity_pass_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('-P', '--teamcity_pass', action='store', required=True,
                        help='The TeamCity URL Password')


def add_teamcity_url_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('-T', '--teamcity_url', action='store', required=True,
                        help='The TeamCity URL')


def add_skip_old_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('-s', '--skip_old', action='store_true',
                        help='Skip builds if a artifacts.json is found. Used to skip builds that have already been '
                             'synced')


def get_project_ids(project_root: str, teamcity_url: str, teamcity_user: str, teamcity_pass: str) -> List[str]:
    result = []
    r = requests.get("{}/app/rest/projects/id:{}?fields=projects(project(id))".format(teamcity_url, project_root),
                     headers={"Accept": "application/json"}, auth=(teamcity_user, teamcity_pass))
    j = r.json()
    for project in j['projects']['project']:
        i = project['id']
        result.append(i)
        result.extend(get_project_ids(
            i, teamcity_url, teamcity_user, teamcity_pass))
    return result


def build_results_iter(local_artifact_root: str, project_root: str, teamcity_url: str, teamcity_user: str, teamcity_pass: str) -> Generator[str, None, None]:
    project_ids = get_project_ids(
        project_root, teamcity_url, teamcity_user, teamcity_pass)
    for project_id in sorted(project_ids):
        local_project_dir = os.path.join(local_artifact_root, project_id)
        if (not os.path.isdir(local_project_dir)):
            continue

        if project_id.startswith('_'):
            continue

        for build_config in sorted(os.listdir(local_project_dir)):
            local_build_config_dir = os.path.join(
                local_project_dir, build_config)

            for build_result in sorted(os.listdir(local_build_config_dir), key=int):
                build_result_dir = os.path.join(
                    local_build_config_dir, build_result)
                print(build_result_dir)

                yield build_result_dir


def get_artifact_list(build_result_dir: str) -> List[str]:
    artifact_list = []
    for root, dirs, files in os.walk(build_result_dir):
        # Skip Teamcity directory, it is not a artifact
        if '/.teamcity/' in root or root.endswith('/.teamcity'):
            continue
        for file in files:
            full_path = os.path.join(root, file)
            assert os.path.isfile(full_path), \
                "  Found something that is not a file, {}".format(full_path)
            artifact_list.append(full_path)
    return artifact_list


if '__main__' == __name__:
    print('You probably did not mean to invoke this file. Try again.', file=sys.stderr)
