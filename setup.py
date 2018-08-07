import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

requires = [
    'SQLAlchemy',
    'pyramid',
    'python-rapidjson',
]
extra_require = {
    # 'all': ['sqlacodegen?', 'alembic?'],
    'test': ['pytest'],
    'docs': ['sphinx'],
}

setuptools.setup(
    name="restalchemy",
    version="0.1a1",

    author="Daniel Kraus",
    author_email="daniel@kraus.my",

    description="Rest api sqlalchemy",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dakra/restalchemy",
    license='ISC',
    packages=setuptools.find_packages(),
    classifiers=(
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: ISC License (ISCL)',
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        'Topic :: Internet',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ),
    keywords='pyramid sqlalchemy rest json api',
    setup_requires=['setuptools_git'],
    install_requires=requires,
    extras_require=extra_require,
)
