FAQ
===

Warum bleiben meine Formularfelder leer, wenn ich sie befülle?
--------------------------------------------------------------

Es gibt unterschiedliche Möglichkeiten für dieses Ergebnis:

#. Erscheint eine Fehlermeldung? Dann hast du vielleicht hast du einen
   Programmfehler (Bug) gefunden. Teile die Fehlermeldung mit Lukas über Github
   oder andere Kanäle (nachdem du aus der Fehlermeldung alle sensiblen Daten
   entfernt hast).

#. Fehlen die Daten auch dann, wenn du die PDF-Datei mit dem Firefox-Browser als
   PDF-Reader geöffnet hast? Manche PDF-Reader zeigen die Inhalte von
   Formularen nicht korrekt an.

#. Stimmen die Namen der Formular-Felder mit den Variablennamen in der
   Datenbank überein?

Wie greife ich auf Backups zu?
------------------------------

Rufe ``edupsyadmin`` in dem Ordner auf, in dem das Backup liegt.
Mit dem Befehl ``ls`` kannst du überprüfen, ob in dem Ordner in dem du
``edupsyadmin`` aufrufst, ``salt.txt``, ``edupsyadmin.db`` und
``config.yml`` liegen. Wenn nicht, bist du vielleicht im falschen Ordner
und musst mit ``cd "pfad/deiner/sicherung/"`` noch an die richtige Stelle
in deinem Dateisystem gehen.

Damit ``edupsyadmin`` nicht die aktuellen Dateien, sondern das Backup
verwendet, musst du auf die Dateien (Salt, Datenbank und Konfigurationsdatei)
verweisen in jedem Befehl. Hier ist zum Beispiel der Befehl, um die Klienten
in der Datenbank anzuzeigen (``get_clients``):

.. code-block:: console

    $ edupsyadmin --config_path "./config.yml" get_clients \
        --salt_path "./salt.txt" \
        --database_url "sqlite:///edupsyadmin.db"
