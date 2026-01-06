Kommandozeile
=============

Während die :doc:`interaktive Benutzeroberfläche (TUI) <tui>` für die tägliche
Arbeit mit einzelnen Klienten optimiert ist, bietet die Kommandozeile (CLI)
mächtige Werkzeuge für fortgeschrittene Anwender. Die CLI eignet sich
hervorragend für die Automatisierung von wiederkehrenden Aufgaben und die
Bearbeitung von Daten für mehrere Klienten gleichzeitig.

Alle hier gezeigten Befehle können in Skripten verwendet werden, um
Arbeitsabläufe zu automatisieren.

Klienten hinzufügen (``new_client``)
------------------------------------

Während ``edupsyadmin new_client`` ohne weitere Argumente die TUI zum Bearbeiten
startet, liegt die Stärke der Kommandozeile im Import von Daten. Stell dir vor,
du hast eine CSV-Datei exportiert, z.B. aus WebUntis. Anstatt die Daten
manuell einzugeben, können wir sie direkt importieren.

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

``--inject_data``: Falls nötig, können hiermit Daten nur für diesen einen
Ausfüllvorgang überschrieben oder hinzugefügt werden.

.. code-block:: console

    $ edupsyadmin create_documentation 1 --form_set lrst --inject_data "today_date_de=16.10.2025"

Klienten löschen (``delete_client``)
------------------------------------

Löscht einen (oder mehrere) Klienten unwiderruflich aus der Datenbank.

.. code-block:: console

    $ edupsyadmin delete_client 1
