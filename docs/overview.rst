Overview
========

The project is split into clear layers:

* ``app.api`` handles HTTP endpoints and FastAPI dependencies.
* ``app.bot`` contains the Telegram interface.
* ``app.services`` contains email analysis and LLM clients.
* ``app.repositories`` contains database access.
* ``app.db`` contains SQLAlchemy configuration and models.
* ``app.core`` contains settings and queue helpers.
* ``app.workers`` contains background RQ tasks.

The main design goal is to keep interfaces thin. FastAPI, Telegram, and
RQ workers reuse the same service layer instead of duplicating analysis
logic.
