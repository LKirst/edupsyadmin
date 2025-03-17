Einstieg
========

.. tip::

    Einige Schritte in diesem Einstieg mögen kompliziert wirken, aber sie müssen
    **nur einmal**, beim ersten Einrichten durchgeführt werden. Also nicht
    einschüchtern lassen!

.. note::

    edupsyadmin lässt sich auf Windows, MacOS und Linux installieren. Die folgende
    *Installationsanleitung bezieht sich auf Windows*. Ich hoffe, Information für
    die anderen Betriebssysteme in der Zukunft zu ergänzen.

Installation
------------

Als erstes öffne ein Terminal. Auf Windows, drücke dafür die Tasten
:kbd:`Win-X`. Dann wähle "Windows Powershell" oder "(Windows) Terminal". Es
sind keine Administratorrechte nötig.

Zur Installation verwenden wir winget. Kontrolliere zunächst, ob winget
installiert ist:

.. note::

    Das `$` Zeichen in den folgenden Anleitungen steht dafür, dass in der
    Kommandozeile ein Befehl eingegeben werden muss. Es ist nicht Teil des
    Befehls und muss nicht mit eingegeben werden.

.. code-block:: console

    $ winget --help

Wenn ein Hilfe-Text und keine Fehlermeldung erscheint, ist winget installiert.
Mit winget kannst du uv installieren:

.. code-block:: console

    $ winget install --id=astral-sh.uv  -e

Damit du uv verwenden kannst, musst du das Terminal *einmal schließen und wieder
öffnen*. uv erlaubt dir, edupsyadmin zu installieren:

.. code-block:: console

   $ uv tool install edupsyadmin

Dieser Befehl zeigt wahrscheinlich eine Warnung wie unten an, wobei dein Pfad
anders aussehen wird:

.. code-block:: console

   $ uv tool install edupsyadmin
   warning: `C:\Users\DeinNutzername\.local\bin` is not on your PATH. To use installed tools run `$env:PATH = "C:\\Users\\DeinNutzername\\.local\\bin;$env:PATH"`.

Der vorgeschlagene Befehl (``$env:PATH =
"C:\\Users\\DeinNutzername\\.local\\bin;$env:PATH"``) macht edupsyadmin
verfügbar für diese Sitzung. Wir wollen aber, dass edupsyadmin dauerhaft
verfügbar ist. Dafür fügen wir den Pfad dauerhaft zur PATH-Umgebungsvariable
hinzu.

1. Kopiere den Pfad aus der Warnung. Im Beispiel oben wäre dieser
   ``C:\Users\DeinNutzername\.local\bin``

2. Drücke die Tasten :kbd:`Win-S`, um die Suche zu öffnen.

3. Gebe in die Suche ein "Umgebungsvariablen für dieses Konto bearbeiten" und
   wähle den Vorschlag mit der höchsten Übereinstimmung aus.

4. In dem Fenster das sich öffnet, klicke unter "Benutzervariablen" die Zeile
   mit ``Path`` an, sodass sie blau hinterlegt ist.

5. Wähle darunter ``Bearbeiten`` aus (im Abschnitt zu Benutzervariablen,
   *nicht* im Abschnitt zu Systemvariablen).

6. In dem Fenster, das sich öffnet, wähle rechts ``Neu`` und füge dann links den
   Pfad ein, den du in Schritt 1 kopiert hast.

7. Klicke in beiden noch offenen Fenstern ``OK``.

8. Öffne und schließe das Terminal.

Nun sollte edupsyadmin immer verfügbar sein, was du testen kannst mit:

.. code-block:: console

   $ edupsyadmin --help

Wenn eine Hilfe-Nachricht erscheint, ist die Installation gelungen.

Konfiguration
-------------

Zuerst musst du die Konfigurationsdatei mit deinen Daten aktualisieren. Um die
Konfigurationsdatei zu finden, führe aus:

.. code-block:: console

   $ edupsyadmin info

Im Ausgabeergebnis siehst du deinen ``config_path``. Öffne die Datei mit einem
Editor, der keine Formatierungen hinzufügt (zum Beispiel Notepad unter
Windows). Ändere alle Werte zu den Daten, die in deiner Dokumentation
erscheinen sollen.

.. caution::

    In dem Yaml-Dateiformat der Konfigurationsdatei haben Leerzeichen Bedeutung.
    Verändere also bitte keine Einrückung (die Anzahl Leerzeichen vor einem Wert).

1. Ersetze zuerst ``sample.username`` durch deinen Benutzernamen (keine Leerzeichen
   und keine Sonderzeichen) in der Zeile mit ``app_username``:

.. code-block::

    app_username: DEIN.NAME

2. Ändere dann deine Daten unter ``schoolpsy``

.. code-block::

    schoolpsy_name: "Schreibe hier deinen Namen aus"
    schoolpsy_street: "Deine Straße und Hausnummer"
    schoolpsy_town: "Postleitzahl und Stadt"

3. Ändere unter ``school`` den Kurznamen deiner Schule zu etwas einprägsamerem
   als ``FirstSchool``. Verwende keine Leerzeichen oder Sonderzeichen:

.. code-block::

    MeinEinpraegsamerSchultitel`

4. Füge die Daten für deine Schule hinzu. Die Variable ``end`` wird verwendet, um
   das Datum für die Vernichtung der Unterlagen (3 Jahre nach dem
   voraussichtlichen Abschlussdatum) zu schätzen. Es benennt die
   Jahrgangsstufe, nach der die Schüler:innen typischerweise die Schule
   verlassen.

.. code-block::

    school_head_w_school: "Titel deiner Schulleitung"
    school_name: "Name deiner Schule ausgeschrieben"
    school_street: "Straße und Hausnummer deiner Schule"
    school_town: "Postleitzahl und Stadt"
    end: 11

5. Wiederhole Schritt 3 und 4 für jede Schule, an der du tätig bist.

6. Ändere die Pfade unter filesets, um auf die (Sets von) Dateien zu
   verweisen, die du verwenden möchtest.

.. code-block::

    fileset:
        name_meines_filesets:
            - "pfad/zu/meiner/ersten_datei.pdf"
            - "pfad/zu/meiner/zweiten_datei.pdf"

Anmeldedaten speichern
----------------------

edupsyadmin verwendet ``keyring`` für die Verschlüsselungsanmeldedaten.
``keyring`` hat mehrere Backends. Unter Windows ist der Standard der Windows
Credential Manager (Deutsch: Anmeldeinformationsverwaltung).

1. Drücke dafür die Tasten :kbd:`Win-S`. Dann suche nach
   "Anmeldeinformationsverwaltung" und öffne sie.

2. Wähle ``Windows-Anmeldeinformationen``.

3. Wähle ``Windows-Anmeldeinformationen hinzufügen``.

4. Verwende den Benutzernamen aus deiner config.yaml Datei und lege ein
   Passwort fest. Die Internet- oder Netzwerkadresse kannst du wie unten übernehmen.

    Internet- oder Netzwerkadresse: ``liebermann-schulpsychologie.github.io``

    Benutzername: ``der_nutzer_name_aus_der_konfigurationsdatei``

    Kennwort: ``ein_sicheres_passwort``
