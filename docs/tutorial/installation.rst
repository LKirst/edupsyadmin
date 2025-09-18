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

Voraussetzungen
---------------

Terminal
^^^^^^^^

Edupsyadmin wird in einem Terminal aufgerufen. Dafür muss ein modernes
Terminal installiert sein.

Auf Windows ist dies **Windows Terminal**, das seit Win11 meist vorinstalliert
ist. Ist es nicht vorhanden, kann es über den `Microsoft Store installiert
werden <https://aka.ms/terminal>`__.

Auch MacOS hat eine Terminal App vorinstalliert, mit der edupsyadmin
funktioniert. Für die beste user experience ist aber empfohlen, ein moderneres
Terminal zu installieren wie `gostty <https://ghostty.org/>`__, `kitty
<https://sw.kovidgoyal.net/kitty/>`__, `westerm <https://wezterm.org/>`__ oder
`iTerm2 <https://iterm2.com/features.html>`__

uv (auf Windows)
^^^^^^^^^^^^^^^^

.. note:: Die :kbd:`Win` Taste ist die Taste mit dem Windows Symbol |WinKey|.

.. |WinKey| unicode:: U+229E

Als erstes öffne ein Terminal. Auf Windows, drücke dafür die Tasten
:kbd:`Win-X`. Dann wähle "(Windows) Terminal". Es
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

    $ winget install --id=astral-sh.uv  -e --source winget

Damit du uv verwenden kannst, musst du das Terminal *einmal schließen und
wieder öffnen*.

uv (MacOS)
^^^^^^^^^^

1. Öffne das Terminal deiner Wahl über eine Suche nach Terminal im Launchpad.

1. Gebe ein: `curl -LsSf https://astral.sh/uv/install.sh | sh`

   Sollte der Befehl nicht funktionieren, gebe ein:
   `wget -qO- https://astral.sh/uv/install.sh | sh`

Installation
------------

uv erlaubt dir, edupsyadmin zu installieren:

.. code-block:: console

   $ uv tool install edupsyadmin

Dieser Befehl zeigt wahrscheinlich eine Warnung wie unten an, wobei dein Pfad
anders aussehen wird:

.. code-block:: console

   $ uv tool install edupsyadmin
   warning: `C:\Users\DeinNutzername\.local\bin` is not on your PATH. To use installed tools run `$env:PATH = "C:`\Users`\DeinNutzername`\.local`\bin;$env:PATH"` or `uv tool update-shell`.

Der vorgeschlagene Befehl (``$env:PATH =
"C:`\Users`\DeinNutzername`\.local`\bin;$env:PATH"``) macht edupsyadmin
verfügbar für diese Sitzung. Wir wollen aber, dass edupsyadmin dauerhaft
verfügbar ist. uv bietet dafür einen eigenen Befehl, den wir als erstes
versuchen:

.. code-block:: console

    $ uv tool update-shell

Schließe und öffne das Terminal wieder. Nun sollte edupsyadmin immer verfügbar sein,
was du testen kannst mit:

.. code-block:: console

   $ edupsyadmin --help

Wenn eine Hilfe-Nachricht erscheint, ist die Installation gelungen. Erscheint
ein Fehler, können wir den Pfad auf Windows auch selbst hinzufügen mit den folgenden
Schritten:

1. Kopiere den Pfad aus der Warnung. Im Beispiel oben wäre dieser
   ``C:\Users\DeinNutzername\.local\bin`` (ohne ``;$env:PATH``). Wenn in dem
   Pfad noch das Zeichen ````` auftaucht vor den Backslashs ``\``, dann
   entferne es.

1. Drücke die Tasten :kbd:`Win-S`, um die Suche zu öffnen.

1. Gebe in die Suche ein "Umgebungsvariablen für dieses Konto bearbeiten" und
   wähle den Vorschlag mit der höchsten Übereinstimmung aus.

1. In dem Fenster das sich öffnet, klicke unter "Benutzervariablen" die Zeile
   mit ``Path`` an, sodass sie blau hinterlegt ist.

1. Wähle darunter ``Bearbeiten`` aus (im Abschnitt zu Benutzervariablen,
   *nicht* im Abschnitt zu Systemvariablen).

1. In dem Fenster, das sich öffnet, wähle rechts ``Neu`` und füge dann links den
   Pfad ein, den du in Schritt 1 kopiert hast.

1. Klicke in beiden noch offenen Fenstern ``OK``.

1. Öffne und schließe das Terminal, um dann mit ``edupsyadmin --help`` die
   Installation zu testen.

Hintergrund zu den Verschlüsselungsdaten
----------------------------------------

In der Datenbank von edupsyadmin auf deinem Rechner sind bestimmte
personenbezogene Daten verschlüsselt und werden bei der Ausführung eines
Befehls von edupsyadmin vorrübergehend entschlüsselt (alle Variablen, deren
Name auf "_encr" endet, s. Dokumentation der Datenbank).

Standard Backends
^^^^^^^^^^^^^^^^^

edupsyadmin verwendet ``keyring``, um die Verschlüsselungsdaten zu speichern.
``keyring`` hat mehrere Backends. Unter Windows ist der Standard Windows
Credential Manager (Deutsch: Anmeldeinformationsverwaltung), auf macOS Keychain
(Deutsch: Schlüsselbund).

Wenn du den Windows Credential Manager verwendest, sollte dein Rechner mit
einem guten Passwort geschützt und nur für dich zugänglich sein, denn
jeder, der die Login Daten für deinen Rechner kennt, hat damit Zugriff auf
deine Anmeldeinformationsverwaltung und auf die dort gespeicherten
Verschlüsselungsdaten für edupsyadmin. Jenachdem wie du edupsyadmin
nutzt, ist das Bitwarden Backend eine sicherere Alternative (s.u.).

Standardmäßig gilt dasselbe für den macOS Keychain, wobei hier ein vom
Login separates Password für Keychain gesetzt werden kann, was die Sicherheit
erhöht.

Bitwarden Backend
^^^^^^^^^^^^^^^^^

Eine für alle Betriebssysteme mögliche Alternative ist die Bitwarden CLI. Sie
erfordert vor jeder Nutzung von edupsyadmin, dass der Zugang zum Password für
die Sitzung entschlüsselt werden, was die Sicherheit erhöht. Dafür musst du:

- ein Bitwarden-Konto anlegen: `<https://bitwarden.com>`_
- die Bitwarden CLI installieren: `<https://bitwarden.com/help/cli/>`_
- edupsyadmin mit dem optionalen Paket bitwarden-keyring installieren:

.. code-block :: console

  uv tool install --with bitwarden-keyring edupsyadmin

- dich einmalig in der Shell (z.B. Powershell über das Windows Terminal) einloggen:

.. code-block :: console

  bw login

- vor jeder Sitzung Bitwarden mit dem für Bitwarden gesetzten
  Passwort entschlüsseln

.. code-block :: console

  bw unlock

- den von ``bw unlock`` generierten Sitzungsschlüssel in die Shell  (``export
  BW_SESSION=...`` für Bash oder ``$env:BW_SESSION=...`` für Powershell)

- nach der Sitzung den Zugang wieder verschlüsseln mit ``bw lock``


Konfiguration und Verschlüsselungsdaten festlegen
-------------------------------------------------

Zuerst musst du die Konfiguration mit deinen Daten aktualisieren. Führe dafür
folgenden Befehl aus:

.. code-block:: console

   $ edupsyadmin edit_config

Für die meisten Eingabefelder ist in dieser Ansicht eine Erklärung hinterlegt,
die sichtbar wird, wenn du die Maus darüber bewegst.

1. Ersetze ``sample.username`` durch deinen Benutzernamen (keine Leerzeichen
   und keine Sonderzeichen) unter App-Einstellungen:

.. code-block:: text

    DEIN.NAME

1. Lege einmalig ein sicheres Passwortsicheres Passwort  fest. Das Passwort solltest du für eine bestehende
   Datenbank nicht ändern, sonst können die Daten nicht mehr entschlüsselt werden.

.. code-block:: text

    ein_sicheres_passwort

1. Ändere dann deine Daten in den Schulpsychologie-Einstellungen:

.. code-block:: text

    Postleitzahl und Stadt
    Dein Vor- und Nachname (wie er auf Formularen erscheinen soll)
    Die Straße und Hausnummer deiner Stammschule

1. Ändere unter "Einstellungen für Schule 1" den Kurznamen deiner Schule zu
   etwas einprägsamerem als ``FirstSchool``. Verwende keine Leerzeichen oder
   Sonderzeichen. In diesem Tutorial verwenden wir den Schulnamen
   ``TutorialSchule``.

.. code-block:: text

    TutorialSchule

1. Füge die Daten für deine Schule hinzu. Die Variable ``end`` wird verwendet, um
   das Datum für die Vernichtung der Unterlagen (3 Jahre nach dem
   voraussichtlichen Abschlussdatum) zu schätzen. Sie benennt die
   Jahrgangsstufe, nach der die Schüler:innen typischerweise die Schule
   verlassen.

.. code-block:: text

    11
    300
    Postleitzahl und Stadt
    Straße und Hausnummer der Schul
    Titel deiner Schulleitung
    Name der Schule ausgeschriebe

1. Über den Button ``Schule hinzufügen`` können weitere Schulen hinzugefügt
   werden. Wiederhole die zwei letzten Schritte für jede Schule, an der du tätig bist.

1. Ändere die Pfade unter ``form_set``, um auf die (Sets von) PDF-Formularen zu
   verweisen, die du verwenden möchtest. Bitte lade für unser Beispiel folgende
   zwei Beispiel-PDFs herunter und speichere Sie:

    Erste Datei: `sample_form_mantelbogen.pdf
    <https://github.com/LKirst/edupsyadmin/blob/main/test/edupsyadmin/data/sample_form_mantelbogen.pdf>`_.

    Zweite Datei `sample_form_stellungnahme.pdf
    <https://github.com/LKirst/edupsyadmin/blob/main/test/edupsyadmin/data/sample_form_stellungnahme.pdf>`_.

    Im Explorer, klicke mit der rechten Maustaste auf eine Datei und wähle "Als
    Pfad kopieren". Kopiere den Pfad in ein form_set. Unser form_set nennen wir für diese Tutorial
    ``tutorialset``.

.. code-block:: text

    pfad/zu/meiner/ersten_datei/sample_form_mantelbogen.pdf
    pfad/zu/meiner/zweiten_datei/sample_form_stellungnahme.pdf

1. Speichere die Änderungen.
