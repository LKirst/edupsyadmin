Dokumentation erstellen
-----------------------

Fülle ein PDF-Formular für den Datenbankeintrag mit ``client_id=42``:

.. code-block:: console

    $ edupsyadmin create_documentation 42 ./pfad/zu/deiner/datei.pdf

Fülle alle Dateien, die zum Formulartyp ``lrst`` gehören (wie in der
config.yml definiert), mit den Daten für ``client_id=42``:

.. code-block:: console

    $ edupsyadmin create_documentation 42 --form_set lrst
