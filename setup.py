from pathlib import Path

import setuptools

root_dir = Path(__file__).absolute().parent
with (root_dir / "VERSION").open() as f:
    version = f.read()
with (root_dir / "README.md").open() as f:
    long_description = f.read()
with (root_dir / "requirements.txt").open() as f:
    requirements = f.read().splitlines()


setuptools.setup(
    name="calculatrice_monitoring",
    version=version,
    description="External module 'calculatrice_monitoring' for GeoNature",
    long_description=long_description,
    long_description_content_type="text/markdown",
    maintainer="",
    maintainer_email="",
    url="https://github.com/PnX-SI/calculatrice_monitoring",
    packages=setuptools.find_packages("backend"),
    package_dir={"": "backend"},
    package_data={},
    install_requires=requirements,
    zip_safe=False,
    entry_points={
        "gn_module": [
            "code = calculatrice_monitoring:MODULE_CODE",
            "picto = calculatrice_monitoring:MODULE_PICTO",
            "blueprint = calculatrice_monitoring.blueprint:blueprint",
            "migrations = calculatrice_monitoring:migrations",
            "alembic_branch = calculatrice_monitoring:ALEMBIC_BRANCH",
        ],
    },
    classifiers=[],
)
