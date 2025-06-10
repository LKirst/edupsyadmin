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
Die Datei kannst du speichern, indem du :kbd:`Strg-S` klickst. Wir ordnen den
Schüler unserer, in der Konfiguration angelegten ``TutorialSchule`` zu.

.. code-block:: console

    $ edupsyadmin new_client --csv "./pfad/zu/samblewebuntisfile.csv" --name "MustermMax1" --school TutorialSchule

Einträge bearbeiten
-------------------

Ändere Werte für den Datenbankeintrag mit ``client_id=2``. Wenn du oben
``MustermMax1`` als zweites hinuzgefügt hast, ist hat er die ID ``2``. Hierbei
steht ``1`` für "wahr/ja" und ``0`` für "falsch/nein".

.. code-block:: console

    $ edupsyadmin set_client 2 \
      "nta_font=1" \
      "nta_zeitverl_vieltext=20" \
      "nos_rs=0" \
      "lrst_diagnosis=iLst"

Einträge anzeigen
-----------------

Zeige eine Übersicht aller Klienten in der Datenbank an:

.. code-block:: console

    $ edupsyadmin get_clients

Hier sollten nun die zwei hinzugefügten Klienten angezeigt werden. In der
ersten Spalte ist die ``client_id`` gelistet.

Zeige alle Daten für einen einzelnen Klienten an:

.. code-block:: console

    $ edupsyadmin get_clients --client_id 2

Hier sollten nun alle Daten für ``client_id=2`` gelistet sein, auch die
oben geänderten Felder wie ``nta_font``.

Einträge löschen
----------------

Lösche den Eintrag mit ``client_id=1``:

.. code-block:: console

    $ edupsyadmin delete_client 1

Mit ``edupsyadmin get_clients`` kannst du nun prüfen, ob der Eintrag entfernt wurde.
