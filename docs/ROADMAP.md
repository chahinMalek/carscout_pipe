# Roadmap

This document serves as the project roadmap for CarScout Pipeline, outlining current priorities, planned features, and future goals.

## 🚀 Current Priorities (Improvements)
- [ ] **Architecture**: Upgrade to SQLAlchemy 2.0+ & add Alembic migrations.
- [ ] **Observability**: Improve error handling and observability in DAGs.
- [ ] **CI/CD**: Implement GitHub Actions CI workflows.
- [ ] **Quality**: Add repository badges (tests, coverage, code quality) & architecture diagrams.

## 🛠 Planned Features
- [ ] **Interface**: Simple CLI entrypoint & Streamlit dashboard.
- [ ] **Proxies**: Integrating proxy providers (opt-in via configs).
    - Adapters for ZenRows, ScrapingBee, and custom lists.
    - Health checks and automatic fallback capabilities.
- [ ] **Data Export**: Add capabilities for CSV, JSON, and Parquet exports.

## 🔮 Future / Potential Features
- [ ] **Scraping Engine**: Migration to Playwright for faster scraping.
- [ ] **Analytical Storage**: Explore DuckDB as an alternative for analytical queries.
