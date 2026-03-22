Update
======

.. caution::

    Wenn du mit einem bestehenden Datensatz updatest, informiere dich
    vorher, ob von deiner Version auf die neue Version sogenannte "breaking
    changes" durchgeführt wurden, d.h. Änderungen, die zu Inkompatibilitäten
    von deiner Datenbank zur neuen Version der App führen.

    Ein verlässlicher Hinweis dafür, dass keine breaking changes durchgeführt
    wurden und einem Update mit Migration der Daten nichts im Wege steht, ist
    dass sich die erste Ziffer in der Version nicht von der installierten auf
    die neue Version geändert hat. Das kannst du auf `PYPI
    <https://pypi.org/project/edupsyadmin/#history>`_ prüfen.

Um keine Dateien zu überschreiben, hat edupsyadmin in früheren Versionen für
jede Version einen eigenen Unterordner für Konfigurationsdatei und Datenbank
erstellt. Ab Version 9.0.0 werden diese Daten automatisch in einen stabilen
Ordner migriert, damit bei zukünftigen Updates keine manuellen Schritte mehr
nötig sind.

Bei jedem Update, das eine Datenbank-Migration erfordert, erstellt edupsyadmin
automatisch ein Backup der Datenbank unter ``edupsyadmin.db.bak`` im selben
Ordner.

.. warning::

    Backups müssen manuell gelöscht werden, sobald das Update erfolgreich
    abgeschlossen wurde, um den Datenschutz zu gewährleisten. Wenn zum
    Beispiel ein Klient gelöscht wird, bleibt dessen Datensatz im Backup
    weiterhin bestehen, bis die Backup-Datei gelöscht wird.

Überprüfe mit folgendem Befehl, wo deine Dateien liegen und ob ein Backup
existiert:

.. code-block:: console

   $ edupsyadmin info

Update der App
--------------

Aktualisiere vor dem Update uv und python:

.. tab-set::
    :sync-group: update-os

    .. tab-item:: Windows
        :sync: windows-os

        .. code-block:: console

           $ winget upgrade uv
           $ uv python upgrade

    .. tab-item:: macOS und Linux
        :sync: macos-linux-os

        .. code-block:: console

           $ uv self update
           $ uv python upgrade


Nun aktualisiere edupsyadmin mit:

.. code-block:: console

   $ uv tool upgrade edupsyadmin --python 3.14

Mit ``edupsyadmin --version`` kannst du überprüfen, welche Version von
edupsyadmin jetzt installiert ist.

Nach dem Update migriert edupsyadmin deine Daten beim ersten Start automatisch
an den neuen, stabilen Speicherort. Du musst keine Dateien mehr manuell
verschieben.
