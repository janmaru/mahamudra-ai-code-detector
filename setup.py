from setuptools import setup, find_packages

setup(
    name="mahamudra-ai-code-detector",
    version="0.1.0",
    description="Analyze Git repositories to estimate where AI coding assistants were involved",
    author="Mahamudra",
    license="MIT",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.9",
    install_requires=[
        "GitPython>=3.1.40",
        "pydantic>=2.0.0",
        "pandas>=2.0.0",
        "PyYAML>=6.0",
        "click>=8.1.0",
        "tabulate>=0.9.0",
        "colorama>=0.4.6",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "mahamudra-detector=mahamudra_ai_code_detector.cli:main",
            "mahamudra-detector-ui=mahamudra_ai_code_detector.ui.app:main",
        ]
    },
)
