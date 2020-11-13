ARG PYTHON_VERSION=3.8

FROM python:${PYTHON_VERSION} AS build

# install dependencies
RUN pip install --upgrade pip
COPY requirements*.txt /app/
RUN for reqs in /app/requirements*.txt; do pip install --no-cache-dir -r $reqs; done

# configure and executes build
COPY . /app
WORKDIR /app
# TODO: Add pydocstyle integration
#RUN pydocstyle ${MODULE_NAME}/
RUN echo "Running setup tools..." \
    && python setup.py \
        pylint \
        isort \
        flake8 \
        pytest \
        sdist \
        bdist_wheel \
    && export CI=True \
    && echo "Finished running setup tools..."

RUN echo "Running mypy static analysis tool..." \
    && mypy gitinsights

RUN echo "Running unit tests..." \
    && pytest gitinsights

# executes code coverage upload to codecov.io
CMD ["/bin/bash", "-c", "bash <(curl -s https://codecov.io/bash)"]
