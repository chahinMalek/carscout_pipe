# Roadmap

This document serves as the project roadmap for CarScout Pipeline, outlining current priorities, planned features, and future goals.

## 🛠 For Alpha Release
- [x] **Architecture**: Add Alembic migrations.
- [x] **Observability**: Improve error handling and observability in DAGs.
- [x] **CI/CD**: Implement GitHub Actions CI workflows.
- [x] **Quality**: Add repository badges (tests, coverage, code quality) & architecture diagrams.
- [x] **Streamlit Interface**: Dashboard and data export capabilities.
- [ ] **Test Coverage**: Achieve test coverage of at least 90%.

## 🔮 Future / Potential Features
- [ ] **Proxies**: Integrating proxy providers (opt-in via configs).
    - Adapters for ZenRows, ScrapingBee, and custom lists.
    - Health checks and automatic fallback capabilities.
- [ ] **Scraping Engine**: Migration to Playwright for faster scraping.
- [ ] **CLI Interface**: Quick launch and Simple CLI entrypoint (one command to run the entire pipeline).
