"""Setup for edit_subs XBlock."""

import os
from setuptools import setup


def package_data(pkg, roots):
    """Generic function to find package_data.

    All of the files under each of the `roots` will be declared as package
    data for package `pkg`.

    """
    data = []
    for root in roots:
        for dirname, _, files in os.walk(os.path.join(pkg, root)):
            for fname in files:
                data.append(os.path.relpath(os.path.join(dirname, fname), pkg))

    return {pkg: data}


setup(
    name='edit_subs-xblock',
    version='0.1',
    description='edit_subs XBlock',   # TODO: write a better description.
    packages=[
        'edit_subs',
    ],
    install_requires=[
        'XBlock',
    ],
    entry_points={
        'xblock.v1': [
            'edit_subs = edit_subs:EditSubsXBlock',
        ]
    },
    package_data=package_data("edit_subs", ["static", "public"]),
)
