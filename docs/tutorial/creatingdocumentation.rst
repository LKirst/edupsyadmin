Dokumentation erstellen
-----------------------

Als Beispieldatei nehmen wir `sample_form_mantelbogen.pdf
<https://github.com/LKirst/edupsyadmin/blob/main/test/edupsyadmin/data/sample_form_mantelbogen.pdf>`_.
Fülle ein PDF-Formular für den Datenbankeintrag mit ``client_id=2``:

.. code-block:: console

    $ edupsyadmin create_documentation 2 "./pfad/zu/sample_form_mantelbogen.pdf"

Fülle alle Dateien, die zum form_set ``tutorialset`` gehören (wie in der
config.yml definiert), mit den Daten für ``client_id=2``:

.. code-block:: console

    $ edupsyadmin create_documentation 2 --form_set tutorialset
