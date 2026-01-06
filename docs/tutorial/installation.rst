Installation
============

Willkommen bei edupsyadmin! Dieses Tutorial führt dich Schritt für Schritt
durch die Einrichtung und die ersten Schritte mit der Anwendung.

.. tip::

    Einige der folgenden Schritte mögen kompliziert wirken, aber sie müssen
    **nur einmal** beim ersten Einrichten durchgeführt werden. Also nicht
    einschüchtern lassen!

.. note::

   Das ``$`` Zeichen in den folgenden Anleitungen steht dafür, dass in der
   Kommandozeile ein Befehl eingegeben werden muss. Es ist nicht Teil des
   Befehls und muss nicht mit eingegeben werden.


Voraussetzungen
---------------

Terminal
^^^^^^^^

``Edupsyadmin`` wird in einem Terminal aufgerufen. Dafür muss ein modernes
Terminal installiert sein.

.. tab-set::
    :sync-group: installation-os

    .. tab-item:: Windows
        :sync: windows-os

        Auf Windows ist das **Windows Terminal** seit Win11 meist vorinstalliert
        Ist es nicht vorhanden, kann es über den
        `Microsoft Store installiert werden <https://aka.ms/terminal>`__.

    .. tab-item:: macOS und Linux
        :sync: macos-linux-os

        MacOS hat zwar eine Terminal App vorinstalliert, mit der ``edupsyadmin``
        funktioniert. Für die beste Interaktion empfehle ich aber, ein moderneres
        Terminal zu installieren wie `gostty <https://gostty.org/>`__, `kitty
        <https://sw.kovidgoyal.net/kitty/>`__, `westerm <https://wezterm.org/>`__ oder
        `iTerm2 <https://iterm2.com/features.html>`__.

        Auf Linux ist ein modernes Terminal schon vorinstalliert.

uv
^^

.. tab-set::
    :sync-group: installation-os

    .. tab-item:: Windows
        :sync: windows-os

        .. note:: Die :kbd:`Win` Taste ist die Taste mit dem Windows Symbol |WinKey|.

        .. |WinKey| unicode:: U+229E

        Als erstes öffne ein Terminal. Auf Windows, drücke dafür die Tasten
        :kbd:`Win-X`. Dann wähle "(Windows) Terminal". Es
        sind keine Administratorrechte nötig.

        Zur Installation verwenden wir winget. Kontrolliere zunächst, ob winget
        installiert ist:

        .. code-block:: console

            $ winget --help

        Wenn ein Hilfe-Text und keine Fehlermeldung erscheint, ist winget installiert.
        Mit winget kannst du uv installieren:

        .. code-block:: console

            $ winget install --id=astral-sh.uv  -e --source winget

        Damit du uv verwenden kannst, musst du das Terminal *einmal schließen und
        wieder öffnen*.


    .. tab-item:: macOS und Linux
        :sync: macos-linux-os

        #. Öffne das Terminal deiner Wahl über eine Suche nach Terminal im Launchpad.
        #. Gebe ein:

           .. code-block:: console

              $ curl -LsSf https://astral.sh/uv/install.sh | sh

           Sollte der Befehl nicht funktionieren (weil ``curl`` nicht
           verfügbar ist), gebe ein:

           .. code-block:: console

              $ wget -qO- https://astral.sh/uv/install.sh | sh

Installation mit uv
-------------------

uv erlaubt dir, edupsyadmin zu installieren:

.. code-block:: console

   $ uv tool install edupsyadmin --python 3.14

Dieser Befehl zeigt wahrscheinlich eine Warnung wie unten an, wobei dein Pfad
anders aussehen wird:

.. code-block:: console

   $ uv tool install edupsyadmin

   warning: C:\Users\DeinNutzername\.local\bin is not on your PATH.
   To use installed tools run
   `$env:PATH = "C:\Users\DeinNutzername\.local\bin;$env:PATH"`
   or `uv tool update-shell`.

Der vorgeschlagene Befehl (``$env:PATH =
"C:\Users\DeinNutzername\.local\bin;$env:PATH"``) macht ``edupsyadmin``
verfügbar für diese Sitzung. Wir wollen aber, dass ``edupsyadmin`` dauerhaft
verfügbar ist. uv bietet dafür einen eigenen Befehl:

.. code-block:: console

    $ uv tool update-shell

Schließe und öffne das Terminal wieder. Nun sollte ``edupsyadmin`` immer
verfügbar sein, was du testen kannst mit:

.. code-block:: console

   $ edupsyadmin --help

Wenn eine Hilfe-Nachricht erscheint, ist die Installation gelungen.

.. dropdown:: Was tun, wenn ein Fehler erscheint? (Windows)

    Wenn ein Fehler erscheint, können wir den Pfad auf Windows auch selbst
    hinzufügen mit den folgenden Schritten:

    #. Kopiere den Pfad aus der Warnung. Im Beispiel oben wäre dieser
       ``C:\Users\DeinNutzername\.local\bin`` (ohne ``;$env:PATH``). Wenn in dem
       Pfad noch das Backtick-Zeichen (`` ` ``) vor den Backslashs (``\``)
       auftaucht, dann entferne es.

    #. Drücke die Tasten :kbd:`Win-S`, um die Suche zu öffnen.

    #. Gebe in die Suche ein "Umgebungsvariablen für dieses Konto bearbeiten"
       und wähle den Vorschlag mit der höchsten Übereinstimmung aus.

    #. In dem Fenster das sich öffnet, klicke unter "Benutzervariablen" die
       Zeile mit ``Path`` an, sodass sie blau hinterlegt ist.

    #. Wähle darunter ``Bearbeiten`` aus (im Abschnitt zu Benutzervariablen,
       *nicht* im Abschnitt zu Systemvariablen).

    #. In dem Fenster, das sich öffnet, wähle rechts ``Neu`` und füge dann
       links den Pfad ein, den du in Schritt 1 kopiert hast.

    #. Klicke in beiden noch offenen Fenstern ``OK``.

    #. Öffne und schließe das Terminal, um dann mit ``edupsyadmin --help`` die
       Installation zu testen.

Verschlüsselung
---------------

Die von ``edupsyadmin`` gespeicherten personenbezogenen Daten der Klienten
werden verschlüsselt. Die Formulare, die von ``edupsyadmin`` gefüllt, werden
sind allerdings **nicht automatisch verschlüsselt**.

Eine Erklärung der Funktionsweise und der verschiedenen Optionen zur
Verschlüsselung findest du im Kapitel zur :doc:`Verschlüsselung <encryption>`.

Konfiguration festlegen
-----------------------

Nach der Installation musst du die Anwendung einmalig konfigurieren. Hier
hinterlegst du deine persönlichen Daten, die Informationen zu deinen Schulen
und die Pfade zu deinen Formularvorlagen.

Eine Anleitung zur Konfiguration findest du im entsprechenden Kapitel:
:doc:`../tutorial/configuration`.
