Konfiguration
=============

Nach der erfolgreichen Installation ist der nächste Schritt die Konfiguration
von ``edupsyadmin``. Diese wird in einer bequemen grafischen Oberfläche
vorgenommen.

Die Konfiguration wird in einer einfachen Textdatei (YAML-Format) gespeichert.
Darin stehen wichtige Einstellungen wie deine Schulen oder Vorlagen-Sets.
Standardmäßig liegt diese Datei unter ``~/.config/edupsyadmin/config.yml``.

Wir müssen diese Datei aber nicht von Hand bearbeiten. Starte einfach die
Konfigurations-TUI mit diesem Befehl:

.. code-block:: console

   $ edupsyadmin edit_config

Die Oberfläche, die du jetzt siehst, sollte so aussehen:

.. image:: ../../test/edupsyadmin/tui/__snapshots__/test_editconfig/test_initial_layout.svg
   :alt: Konfiguration in der TUI bearbeiten
   :width: 100%
   :align: center

Für die meisten Eingabefelder ist in dieser Ansicht eine Erklärung hinterlegt,
die sichtbar wird, wenn du die Maus über den Namen des Feldes bewegst.

Gehen wir die Felder nun Schritt für Schritt durch:

**App-Einstellungen**

#.  **Benutzername**: Ersetze den Platzhalternutzername ``sample.username``
    durch deinen eigenen Benutzernamen. Wähle etwas Kurzes ohne Leerzeichen
    oder Sonderzeichen.
#.  **Passwort**: Lege hier *einmalig* ein sicheres Passwort für die
    Verschlüsselung fest.

    .. warning::
       Ändere dieses Passwort später nicht mehr, wenn du bereits Daten in
       der Datenbank hast! Sonst können die Daten nicht mehr entschlüsselt
       werden.

**Schulpsychologie-Einstellungen**

Hier hinterlegst du deinen Namen und die Adresse deiner Stammschule.

**Schul-Einstellungen**

#.  **Kurzname**: Ändere unter "Einstellungen für Schule 1" den Kurznamen deiner
    Schule zu etwas Einprägsamem wie z.B. ``GS-Muster``. Verwende auch
    hier keine Leerzeichen oder Sonderzeichen.
#.  **Schuldaten**: Fülle die restlichen Informationen für deine Schule aus.
    Besonders das Feld ``end`` ist interessant: Es hilft ``edupsyadmin`` zu
    schätzen, wann die Akten vernichtet werden können (3 Jahre nach dem
    voraussichtlichen Abschluss). Trage hier die typische
    Abgangs-Jahrgangsstufe ein.
#.  **Weitere Schulen**: Wenn du an mehreren Schulen tätig bist, klicke
    einfach auf ``Schule hinzufügen`` und wiederhole die beiden letzten
    Schritte.

**Formular-Sätze (Form Sets)**

Mit Formular-Sätzen (Form Sets) kannst du wiederkehrende Aufgaben
beschleunigen. Ein "Form Set" ist eine Gruppe von PDF-Vorlagen, die du oft
zusammen brauchst (z.B. Anschreiben und Stellungnahme für LRSt). Lösche die
bestehenden Beispiel-Formularsätze und lege ein neues an:

#.  **Beispiel-Set anlegen**: Wir nennen ein Set ``lrst``.

#.  **Vorlagen herunterladen**: Lade dir diese zwei Beispiel-PDFs herunter
    und speichere sie an einem Ort, wo du sie wiederfindest:

    - `sample_form_mantelbogen.pdf`_
    - `sample_form_stellungnahme.pdf`_

#.  **Pfade kopieren**: Klicke im Datei-Explorer mit der rechten Maustaste auf
    eine der heruntergeladenen Dateien und wähle "Als Pfad kopieren". Füge
    diesen Pfad in ein Feld unter deinem ``lrst`` Set ein. Wiederhole das für
    die zweite Datei.

Abschließend klicke auf **Speichern**, um die Konfiguration zu sichern.

.. _`sample_form_mantelbogen.pdf`: https://github.com/LKirst/edupsyadmin/blob/main/test/edupsyadmin/data/sample_form_mantelbogen.pdf
.. _`sample_form_stellungnahme.pdf`: https://github.com/LKirst/edupsyadmin/blob/main/test/edupsyadmin/data/sample_form_stellungnahme.pdf
