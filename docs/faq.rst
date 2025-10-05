FAQ
===

Wie greife ich auf Backups zu?
------------------------------

Rufe edupsyadmin in dem Ordner auf, in dem das Backup liegt.
Mit dem Befehl ``ls`` kannst du überprüfen, ob in dem Ordner in dem du edupsyadmin aufrufst, salt.txt, edupsyadmin.db und config.yml liegen. Wenn nicht, bist du vielleicht im falschen Ordner und musst mit ``cd "pfad/deiner/sicherung/"`` noch an die richtige Stelle in deinem Dateisystem gehen.

Damit edupsyadmin nicht die aktuellen Dateien, sondern das Backup verwendet, musst du auf die Dateien (Salt, Datenbank und Konfigurationsdatei) verweisen in jedem Befehl. Hier ist zum Beispiel der Befehl, um die Klienten in der Datenbank anzuzeigen (get_clients):

.. code-block:: console

    $ edupsyadmin --config_path "./config.yml" get_clients --salt_path "./salt.txt" --database_url "sqlite:///edupsyadmin.db"
