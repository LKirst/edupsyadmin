Tätigkeitsbericht erstellen
===========================

Ein Tätigkeitsbericht kann nur erstellt werden, wenn für alle
Klienten in der Datenbank jeweils eine Kategorie (``keyword_taet_encr``)
festgelegt ist, die Anzahl der Sitzungen (``n_sessions``) und die Dauer der
sitzungen in Minuten (``min_sessions``). Die möglichen keywords sind
beschrieben in :doc:`Mögliche Tätigkeitsbericht-Kategorien
<../taetigkeitsbericht_keywords>`.

Der Befehl ``edupsyadmin taetigkeitsbericht`` erstellt den Bericht.
Als einziges verpflichtendes Argument muss die Anzahl der Anrechnungsstunden
für Schulpsychologie übergeben werden (im Beispiel unten ``3``).

Die Anzahl der Schüler pro Schule wird direkt aus der Konfigurationsdatei
ausgelesen.  Stelle sicher, dass die ``nstudents``-Werte für deine Schulen
in der Konfiguration korrekt eingetragen sind.

.. code-block:: console

  $ edupsyadmin taetigkeitsbericht 3

Dieser Befehl erstellt viele Dateien für den Tätigkeitsbericht, die dann in
einem PDF-Bericht zusammengefasst werden.

Das Beispiel oben geht davon aus, dass Vollzeit 23 Wochenstunden entspricht.
Über die Flag ``--wstd_total`` kann die Wochenstundenanzahl angepasst werden,
damit im Bericht korrekte Angaben gemacht werden zu den Zeitstunden, die den
angegebenen Anrechnungsstunden entsprechen.

.. code-block:: console

   $ edupsyadmin taetigkeitsbericht --wstd_total 28 3
