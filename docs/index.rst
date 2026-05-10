AI Mail Assistant Documentation
===============================

AI Mail Assistant is a Python service for analyzing incoming emails with
an LLM, saving the analysis history, and exposing the workflow through
HTTP API and Telegram.

.. toctree::
   :maxdepth: 2
   :caption: Contents

   overview
   api
   services
   repositories
   schemas
   workers

Quick Checks
------------

Run the main local checks:

.. code-block:: bash

   make check

Build this documentation:

.. code-block:: bash

   make docs
