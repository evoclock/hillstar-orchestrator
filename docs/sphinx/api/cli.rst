Command-Line Interface
======================

The ``hillstar`` CLI provides workflow management commands.

.. code-block:: bash

   hillstar <command> [options]

Commands
--------

``discover``
   Find workflows in a directory.

``validate``
   Validate a workflow file against the schema.

``execute``
   Execute a workflow with full governance and tracing.

``presets``
   List available model presets by provider.

``enforce``
   Run compliance checks on the project.

``wizard``
   Interactive setup wizard for provider configuration.

``mode``
   Show or set governance mode (workflow-required, dev, force).

Usage
-----

.. code-block:: bash

   # Discover workflows
   hillstar discover ./workflows/

   # Validate a workflow
   hillstar validate workflow.json

   # Execute a workflow
   hillstar execute workflow.json --trace

   # Run setup wizard
   hillstar wizard

   # Check compliance
   hillstar enforce
