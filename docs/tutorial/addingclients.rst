Klienten hinzufügen, bearbeiten, anzeigen
=========================================

Klienten hinzufügen
-------------------

Füge einen Klienten interaktiv hinzu:

.. code-block:: console

    $ edupsyadmin new_client

Füge einen Klienten aus einem Webuntis-CSV-Export zur Datenbank hinzu:

.. code-block:: console

    $ edupsyadmin new_client --csv ./pfad/zu/deiner/datei.csv --name "short_name_of_client"

Einträge bearbeiten
-------------------

Ändere Werte für den Datenbankeintrag mit ``client_id=42``. Hierbei steht ``1``
für "wahr/ja" und ``0`` für "falsch/nein".

.. code-block:: console

    edupsyadmin set_client 42 \
      "nachteilsausgleich=1" \
      "notenschutz=0" \
      "lrst_diagnosis=iLst"

Einträge anzeigen
-----------------

Zeige eine Übersicht aller Klienten in der Datenbank an:

.. code-block:: console

    $ edupsyadmin get_clients
