Interaktive Benutzeroberfläche (TUI)
=====================================

Starten der TUI
---------------

Um die interaktive Benutzeroberfläche zu starten, führe den folgenden Befehl aus:

.. code-block:: console

    $ edupsyadmin tui

Ansicht beim Start anpassen
---------------------------

Die in der Übersicht angezeigten Klienten können bereits beim Start der TUI
gefiltert werden.

Der folgende Befehl filtert die Klienten so, dass nur die Klienten angezeigt
werden, die Nachteilsausgleich oder Notenschutz haben und der ``TutorialSchule``
angehören:

.. code-block:: console

    $ edupsyadmin tui --nta_nos --school TutorialSchule

Zusätzlich können die angezeigten Spalten mit ``--columns`` angepasst werden.
Eine Auswahl an Spalten wird immer angezeigt (``client_id``, ``school``,
``last_name_encr``, ``first_name_encr``, ``class_name``). Mit ``--columns``
können weitere Spalten hinzugefügt werden.

Folgender Befehl zeigt zusätzlich die Spalte für ``notes_encr`` und
``lrst_diagnosis_encr`` an:

.. code-block:: console

    $ edupsyadmin tui --columns notes_encr lrst_diagnosis_encr

Übersicht
---------

Nach dem Start erscheint eine Übersicht aller Klienten in der Datenbank auf der
linken Seite. Die rechte Seite ist zunächst leer bis du eine Zeile in der
Übersicht auswählst, oder einen neuen Klienten hinzufügst.

Die Übersichtstabelle kann nach verschiedenen Spalten sortiert werden, um die
Suche zu erleichtern.

Klienten hinzufügen
-------------------

Mit :kbd:`Strg-n` kann ein neuer Klient hinzugefügt werden. Rechts erscheint
ein Formular zur Eingabe des Klienten.

Klienten anzeigen (und bearbeiten)
----------------------------------

Du kannst in der Liste der Klienten links einen Klienten auswählen mit einem
Klick auf eine Zeile in der Tabelle. Der Klient kann dann rechts bearbeitet
werden.

Navigation und Steuerung
------------------------

Die TUI erlaubt die Bedienung mit der Maus, aber bestimmte Shortcuts
beschleunigen die Bedienung:

- **Navigation**: Verwende die Pfeiltasten, um in Listen und Tabellen zu
  navigieren. Mit :kbd:`Tab` springst du zum nächsten Eingabefeld oder Button.

- **Beenden**: Die TUI kann mit :kbd:`Strg-q` beendet werden.

- **Speichern**: :kbd:`Strg-s`
