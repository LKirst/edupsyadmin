Klienten hinzufügen, bearbeiten, anzeigen
=========================================

Klienten hinzufügen
-------------------

Füge einen Klienten interaktiv hinzu:

.. code-block:: console

    $ edupsyadmin new_client

Füge einen weiteren Klienten aus einem Webuntis-CSV-Export zur Datenbank hinzu.
Verwende dafür die Beispieldatei `samplewebuntisfile.csv
<https://raw.githubusercontent.com/LKirst/edupsyadmin/refs/heads/main/docs/_static/samplewebuntisfile.csv>`_.
Die Datei kannst du speichern, indem du :kbd:`Strg-S` klickst.

.. code-block:: console

    $ edupsyadmin new_client --csv ./pfad/zu/samblewebuntisfile.csv --name "MustermMax1"

Einträge bearbeiten
-------------------

Ändere Werte für den Datenbankeintrag mit ``client_id=2``. Wenn du oben
``MustermMax1`` als zweites hinuzgefügt hast, ist hat er die ID ``2``. Hierbei
steht ``1`` für "wahr/ja" und ``0`` für "falsch/nein".

.. code-block:: console

    edupsyadmin set_client 2 \
      "nachteilsausgleich=1" \
      "notenschutz=0" \
      "lrst_diagnosis=iLst"

Einträge anzeigen
-----------------

Zeige eine Übersicht aller Klienten in der Datenbank an:

.. code-block:: console

    $ edupsyadmin get_clients

Hier sollten nun die zwei hinzugefügten Klienten angezeigt werden. In der
ersten Spalte ist die ``client_id`` gelistet.
