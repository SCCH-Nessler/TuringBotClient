# 🤝 Contributing

We welcome contributions to the TuringBotClient! If you'd like to contribute, we recommend using [uv](https://github.com/astral-sh/uv) for dependency management. Ensure you have `uv` installed before proceeding.

## 🏗️ Setting Up for Development

```bash
# Clone the repository
git clone https://github.com/SCCH-Nessler/TuringBotClient.git
# ssh: git clone git@github.com:SCCH-Nessler/TuringBotClient.git
cd TuringBotClient

# if Windows: Set your Python version
uv python install 3.12.9
uv python pin 3.12.9

# Install dependencies and extras
uv sync --all-extras
```

## ✅ Contribution Steps

1. 🍴 Fork the repository.
2. 🌿 Create a feature branch.
3. 🔄 Submit a pull request with a clear description of your changes and an updated version number in the `pyproject.toml` file.