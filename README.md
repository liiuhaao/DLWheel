# DLWheel

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.6%2B-blue)]()

A lightweight deep learning experiment toolkit.

## Installation

```bash
pip install -e .
```

## Usage

```python
import dlwheel

cfg = dlwheel.setup()  # loads config, optional backup
```

```bash
python main.py --backup
python main.py lr=0.1 batch_size=64
```

## CLI

```bash
dlwheel list                    # list experiments
dlwheel show <exp>              # show details
dlwheel diff <exp>              # compare with backup
dlwheel restore <exp> [--to]    # restore code
dlwheel clean --keep 10         # keep latest N
dlwheel rlog [path] [name]      # rename log dir
```

## Configuration

```yaml
# config/default.yaml
lr: 1e-3
batch_size: 32
backup:
  max_file_size: 100MB
  exclude:
    - "data/"
```

Override via CLI:
```bash
python main.py --config=config/exp.yaml lr=0.1
```
