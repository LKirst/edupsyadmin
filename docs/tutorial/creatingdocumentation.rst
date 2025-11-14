Dokumentation erstellen
-----------------------

Als Beispieldatei nehmen wir `sample_form_mantelbogen.pdf
<https://github.com/LKirst/edupsyadmin/blob/main/test/edupsyadmin/data/sample_form_mantelbogen.pdf>`_.
Fülle ein PDF-Formular für den Datenbankeintrag mit ``client_id=2``:

.. code-block:: console

    $ edupsyadmin create_documentation 2 --form_paths "./pfad/zu/sample_form_mantelbogen.pdf"

Fülle alle Dateien, die zum form_set ``tutorialset`` gehören (wie in der
config.yml definiert), mit den Daten für ``client_id=2``:

.. code-block:: console

    $ edupsyadmin create_documentation 2 --form_set tutorialset

``create_documentation`` akzeptiert auch mehrere client_ids was das Arbeiten
beschleunigen kann, wenn viele Fälle gleichzeitig dokumentiert werden müssen.
Im folgenden Beispiel werden die Formulare des Formularsatzes ``lrst``
(definiert in der Konfiguration) für zwei Klienten ausgefüllt:

.. code-block:: console

    $ edupsyadmin create_documentation 1 2 --form_set lrst

Falls nötig können mit ``--inject_data`` Variablen nur für das Ausfüllen
geändert oder hinzugefügt werden. Ein Beispiel wäre, wenn ich ein anderes Datum
für ``today_date_de`` einfüllen will als das heutige Datum:

.. code-block:: console

    $ edupsyadmin create_documentation 1 --form_set lrst --inject_data "today_date_de=16.10.2025"
