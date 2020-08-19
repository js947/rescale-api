from setuptools import setup, find_packages
setup(
    name="Rescale API",
    version="0.1",
    packages=find_packages(),
    scripts=[],
    install_requires=["requests", "keyring"],
    package_data={},
    author="Jeffrey Salmond",
    author_email="jsalmond@rescale.com",
    description="Jeffrey's Rescale API widget",
    keywords="hello world example examples",
    url="http://github.com/js947/rescale-api/",   # project home page, if any
)