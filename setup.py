from setuptools import setup

setup(
    name="Rescale API",
    version="0.1",
    packages=["rescale"],
    scripts=[],
    package_data={},

    install_requires=["requests", "keyring"],
    extras_require={
        'dev': [
            'pandas',
            'keyrings.alt',
        ]
    },

    author="Jeffrey Salmond",
    author_email="jsalmond@rescale.com",
    description="Jeffrey's Rescale API widget",
    keywords="hello world example examples",
    url="http://github.com/js947/rescale-api/",  # project home page, if any
)
