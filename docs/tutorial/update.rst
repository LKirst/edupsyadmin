Update
======

.. caution::

    Aktualisiere edupsyadmin wenn möglich nur, wenn du einen neuen Datensatz
    beginnst.

    Wenn du mit einem bestehenden Datensatz updatest, informiere dich
    vorher, ob von deiner Version auf die neue Version sogenannte "breaking
    changes" durchgeführt wurden, d.h. Änderungen, die zu Inkompatibilitäten
    von deiner Datenbank zur neuen Version der App führen.

    Ein verlässlicher Hinweis dafür, dass keine breaking changes durchgeführt
    wurden und einem Update mit Migration der Daten nichts im Wege steht, ist
    dass sich die erste Ziffer in der Version nicht von der installierten auf
    die neue Version geändert hat. Das kannst du auf `PYPI
    <https://pypi.org/project/edupsyadmin/#history>`_ prüfen.

Um keine Dateien zu überschreiben, erstellt edupsyadmin für jede Version einen
eigenen Unterordner für Kofigurationsdatei und Datenbank. Die Datenbank für die
ältere Version der App wird nicht automatisch gelöscht oder überschrieben. Die
Datenbank, die mit der alten Version erstellt wurde bleibt als Backup bestehen.

.. warning::

    Backups müssen manuell gelöscht werden, wenn zum Beispiel mit einer neuen
    Version der App ein Klient gelöscht wird oder die Verschlüsselung der
    Datenbank aktualisiert wird (z.B. bei einer Änderung des Passworts). Sonst
    bestehen die Daten des gelöschten Klienten weiter im Backup oder Daten des
    Backups sind weiter mit der alten Verschlüsselung gespeichert.

Überprüfe als erstes (vor dem Update), welche Version deine gegenwärtige
Installation hat und wo deine Dateien (d.h. nach dem Update das Backup) liegen:

.. code-block:: console

   $ edupsyadmin info

Falls du die Daten migrieren willst, notiere dir den Text der ausgegeben wird
mit ``edupsyadmin version``, ``database_url`` und ``config_path``.
Auch wenn du die Daten nicht migrieren willst, solltest du dir
die ``database_url`` notieren, damit du das Backup später findest, wenn du es
löschen willst.

.. warning::

    Der Befehl ``edupsyadmin migrate-encryption`` wird mit Version 9.0.0
    entfernt. Wenn du noch eine Datenbank aus Version 7 nutzt, führe die
    Migration auf das neue Verschlüsselungssystem zeitnah durch.

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

Verschieben der Dateien
-----------------------

Mit ``edupsyadmin info`` kannst du nach Aktualisierung der App überprüfen, wo
Konfigurationsdatei und Datenbank für die neue Version liegen (sollten).
Wenn du die Konfigurationsdatei wiederverwenden willst, kannst du sie vom
alten Pfad an den neuen kopieren. Dasselbe kannst du auch für die Datenbank tun.
