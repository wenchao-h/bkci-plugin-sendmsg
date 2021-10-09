# -*- coding: utf-8 -*-

import os

from setuptools import setup, find_packages

BASE_DIR = os.path.realpath(os.path.dirname(__file__))


def parse_requirements():
    """
    @summary: 获取依赖
    """
    reqs = []
    if os.path.isfile(os.path.join(BASE_DIR, "requirements.txt")):
        with open(os.path.join(BASE_DIR, "requirements.txt"), 'r') as fd:
            for line in fd.readlines():
                line = line.strip()
                if line:
                    reqs.append(line)
    return reqs


if __name__ == "__main__":
    setup(
        version="3.0.0",
        name="sendmsg",
        description="",

        cmdclass={},
        packages=find_packages(),
        package_data={'': ['*.txt', '*.TXT', '*.JS', 'test/*']},
        install_requires=parse_requirements(),

        entry_points={'console_scripts': ['sendmsg = sendmsg.command_line:main']},

        author="vincohuang",
        author_email="vincohuang@tencent.com",
        license="Copyright(c)2021-2022 vincohuang All Rights Reserved."
    )