Klienten zur Datenbank hinzufügen
=================================

Erhalte Informationen über den Pfad zur Konfigurationsdatei und den Pfad zur
Datenbank:

.. code-block:: console

    $ edupsyadmin info

Füge einen Klienten interaktiv hinzu:

.. code-block:: console

    $ edupsyadmin new_client

Füge einen Klienten aus einem Webuntis-CSV-Export zur Datenbank hinzu:

.. code-block:: console

    $ edupsyadmin new_client --csv ./path/to/your/file.csv --name "short_name_of_client"

Ändere Werte für den Datenbankeintrag mit ``client_id=42``. Hierbei steht ``1``
für "wahr/ja" und ``0`` für "falsch/nein".

.. code-block:: console

    edupsyadmin set_client 42 \
      "nachteilsausgleich=1" \
      "notenschutz=0" \
      "lrst_diagnosis=iLst"

Zeige eine Übersicht aller Klienten in der Datenbank an:

.. code-block:: console

    $ edupsyadmin get_clients

Fülle ein PDF-Formular für den Datenbankeintrag mit ``client_id=42``:

.. code-block:: console

    $ edupsyadmin create_documentation 42 ./path/to/your/file.pdf

Fülle alle Dateien, die zum Formulartyp ``lrst`` gehören (wie in der
config.yml definiert), mit den Daten für ``client_id=42``:

.. code-block:: console

    $ edupsyadmin create_documentation 42 --form_set lrst

.. note::

   Dieses Tutorial ist in Arbeit. Es werden bald mehr Informationen hinzugefügt.
