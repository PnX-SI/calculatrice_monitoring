import setuptools
from pathlib import Path


root_dir = Path(__file__).absolute().parent
with (root_dir / "VERSION").open() as f:
    version = f.read()
with (root_dir / "README.md").open() as f:
    long_description = f.read()


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
    zip_safe=False,
    entry_points={
        "gn_module": [
            "code = calculatrice_monitoring:MODULE_CODE",
            "picto = calculatrice_monitoring:MODULE_PICTO",
            "blueprint = calculatrice_monitoring.blueprint:blueprint",
            "migrations = calculatrice_monitoring:migrations",
        ],
    },
    classifiers=[],
)
