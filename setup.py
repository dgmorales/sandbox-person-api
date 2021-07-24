import setuptools

setuptools.setup(
    name="personapi",
    version="0.0.1",
    author="Diego Morales",
    author_email="dgmorales@gmail.com",
    description="A small test application recording information about people",
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.0",
)
