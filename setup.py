from setuptools import setup

setup(
    name='Maga',
    version='1.0.0',
    description='A DHT crawler framework using asyncio.',
    long_description=open('README.rst', 'r').read(),
    author='whtsky',
    author_email='whtsky@gmail.com',
    url='https://github.com/whtsky/maga',
    license='BSDv3',
    platforms='any',
    zip_safe=False,
    keywords=['dht', 'asyncio', 'crawler'],
    classifiers=[
        'Environment :: Other Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Cython',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: Implementation :: CPython',
    ],
)
