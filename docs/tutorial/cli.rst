Kommandozeile
=============

Während die :doc:`interaktive Benutzeroberfläche (TUI) <tui>` für die
Arbeit mit einzelnen Klienten optimiert ist, bietet die Kommandozeile (CLI)
Werkzeuge für die Automatisierung von wiederkehrenden Aufgaben und die
Bearbeitung von Daten für mehrere Klienten gleichzeitig.

Alle hier gezeigten Befehle können in Skripten verwendet werden, um
Arbeitsabläufe zu automatisieren.

Klienten hinzufügen (``new_client``)
------------------------------------

Stell dir vor, du hast eine CSV-Datei exportiert, z.B. aus WebUntis. Anstatt
die Daten manuell einzugeben, können wir sie direkt importieren.

Eine Beispieldatei
(`samplewebuntisfile.csv <../_static/samplewebuntisfile.csv>`_)
kannst du hier herunterladen. Speichere sie in deinem Arbeitsverzeichnis.

**Beispiel:** Importiere einen Klienten namens "MustermMax1" aus dieser
CSV-Datei und weise ihn der "TutorialSchule" zu.

.. code-block:: console

  $ edupsyadmin new_client --csv "./samplewebuntisfile.csv" \
      --name "MustermMax1" --school TutorialSchule


- ``--csv``: Pfad zu einer CSV-Datei (z.B. aus WebUntis).

- ``--name``: Der genaue Name des Klienten, wie er in der "name"-Spalte der
  CSV-Datei steht. Dieser Parameter wählt die zu importierende Zeile aus.

- ``--school``: Der Kurzname der Schule, wie er in der
  :doc:`../tutorial/configuration` festgelegt wurde.

- ``--keepfile``: Standardmäßig wird die CSV-Datei nach dem Import gelöscht.
  Diese Option verhindert das.

**Interaktives Anlegen (eines einzelnen Klienten):** Wenn du ``new_client``
ohne Argumente aufrufst, öffnet sich die TUI, um einen neuen Klienten
anzulegen.

Klienten bearbeiten (``set_client``)
------------------------------------

Mit diesem Befehl können die Daten eines oder mehrerer Klienten geändert
werden.

**Interaktive Bearbeitung (einzelner Klient):** Wenn du ``set_client`` nur mit
einer ID aufrufst, öffnet sich die TUI, um diesen einen Klienten zu bearbeiten.

.. code-block:: console

    $ edupsyadmin set_client 2

**Bearbeitung per Kommandozeile (mehrere Klienten):** Stell dir vor, zum neuen
Schuljahr führst du in einem kurzen Zeitraum viele LRSt-Testungen durch und
möchtest für eine Gruppe Nachteilsausgleich und Notenschutz eintragen. Das wäre
in der TUI viel Klickarbeit. Mit einem Befehl erledigst du das für mehrere auf
einmal.

**Beispiel:** Setze für die Klienten mit den IDs 1, 2 und 5 den
Nachteilsausgleich für die Schriftgröße und einen Zeitzuschlag von 25%.

.. code-block:: console

    $ edupsyadmin set_client 1 2 5 --key_value_pairs "nta_font=1" "nta_zeitv_vieltext=25"

- ``client_id``: Eine oder mehrere IDs von Klienten, die bearbeitet werden
  sollen.

- ``--key_value_pairs``: Eine Liste von Schlüssel-Wert-Paaren.

- Für Wahr/Falsch-Felder steht ``1`` für "wahr" und ``0`` für "falsch".


Klienten anzeigen (``get_clients``)
-----------------------------------

Dieser Befehl zeigt entweder eine Übersicht aller Klienten oder die
Detailansicht für einen einzelnen Klienten an.

-   **Übersicht anzeigen**:

    .. code-block:: console

        $ edupsyadmin get_clients

-   **Interaktive Übersicht**: Für eine sortier- und filterbare Tabelle,
    verwende die ``--tui`` Option.

    .. code-block:: console

        $ edupsyadmin get_clients --tui

-   **Gefilterte Daten exportieren**:

    .. code-block:: console

        $ edupsyadmin get_clients --nta_nos --school TutorialSchule --out "gefilterte_liste.csv"

-   **Details für einen einzelnen Klienten**:

    .. code-block:: console

        $ edupsyadmin get_clients --client_id 2


Dokumentation erstellen (``create_documentation``)
--------------------------------------------------

Auch hier kann die Kommandozeile die Arbeit beschleunigen, wenn Dokumente für
viele Fälle gleichzeitig erstellt werden müssen.

- ``client_id``: Eine oder mehrere IDs von Klienten, für die die Dokumentation
  erstellt werden soll. Die Daten dieser Klienten werden aus der Datenbank
  geladen und zum Ausfüllen der Formulare verwendet.

- ``--form_set``: Der Name eines Formular-Sets, das in der Konfigurationsdatei
  definiert ist. Ein Formular-Set ist eine Sammlung von Pfaden zu
  PDF-Formularen oder Liquid-Vorlagen, die gemeinsam ausgefüllt werden sollen.

- ``--form_paths``: Eine Liste von Pfaden zu den Formulardateien, die
  ausgefüllt werden sollen. Dies können PDF-Formulare oder Textdateien sein,
  die `Liquid-Vorlagen <https://jg-rp.github.io/liquid/syntax/>`_ enthalten.

- ``--inject_data``: Eine Liste von Schlüssel-Wert-Paaren im Format
  ``key=value``. Diese Option kann verwendet werden, um vorhandene Daten der
  Klienten (temporär nur für diesen Ausfüllvorgang) zu überschreiben oder neue
  Schlüssel-Wert-Paare hinzuzufügen, die in den Formularen verwendet werden
  können.

- ``--tui``: Öffnet die TUI (Text User Interface) für eine interaktive
  Formularausfüllung. Wenn diese Option verwendet wird, sind die Argumente
  ``client_id``, ``--form_set``, ``--form_paths`` und ``--inject_data`` nicht
  relevant, da die Auswahl interaktiv erfolgt.

.. code-block:: console

    $ edupsyadmin create_documentation 1 2 --form_set lrst --inject_data "today_date_de=16.10.2025"

Klienten löschen (``delete_client``)
------------------------------------

Löscht einen (oder mehrere) Klienten unwiderruflich aus der Datenbank.

.. code-block:: console

    $ edupsyadmin delete_client 1 2

PDF-Formulare für den Druck vorbereiten (``flatten_pdfs``)
----------------------------------------------------------

Für das Drucken ist es manchmal notwendig, ausgefüllte PDF-Formulare so zu
speichern, dass die Felder nicht mehr bearbeitet werden können. Diesen Vorgang
nennt man "Flattening".

**Voraussetzung**: Benötigt **Poppler**. Siehe :doc:`installation` für
Installationsanweisungen.

**Beispiel:** Bereite zwei Formulare für den Druck vor.

.. code-block:: console

   $ edupsyadmin flatten_pdfs ./formular1_ausgefuellt.pdf ./formular2_ausgefuellt.pdf

Ein neues, für den Druck aufbereitetes PDF mit dem Präfix ``print_`` wird
erstellt (z.B. ``print_formular1_ausgefuellt.pdf``).
