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

Edupsyadmin legt für eine neue Version der App eine neue Datenbank an. Die
Datenbank für die ältere Version der App wird nicht automatisch gelöscht oder
überschrieben. Die Datenbank, die mit der alten Version erstellt wurde bleibt
als Backup bestehen.

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
mit ``edupsyadmin version``, ``database_url``, ``config_path`` und
``salt_path``. Auch wenn du die Daten nicht migrieren willst, solltest du dir
die ``database_url`` notieren, damit du das Backup später findest, wenn du es
löschen willst.

Update der App
--------------

Nun aktualisiere edupsyadmin mit:

.. code-block:: console

   $ uv tool upgrade edupsyadmin

Mit ``edupsyadmin --version`` kannst du überprüfen, welche Version von
edupsyadmin jetzt installiert ist.

Verschieben der Dateien
-----------------------

Um keine Dateien zu überschreiben, erstellt edupsyadmin für jede Version einen
eigenen Unterordner für Kofigurationsdatei, Datenbank und Salt (eine Datei, die
für die Verschlüsselung verwendet wird).

Mit ``edupsyadmin info`` kannst du nach Aktualisierung der App überprüfen, wo
Konfigurationsdatei, Datenbank und Salt für die neue Version liegen (sollten).
Wenn du die Konfigurationsdatei wiederverwenden willst, kannst du sie vom
alten Pfad an den neuen kopieren. Dasselbe kannst du auch für Datenbank und
Salt tun (aber nur in Kombination, da die Verschlüsselung der Datenbank nur mit
Salt entschlüsselt werden kann).
