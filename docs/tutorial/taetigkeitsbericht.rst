Tätigkeitsbericht erstellen
===========================

Ein Tätigkeitsbericht kann nur erstellt werden, wenn für alle
Klienten in der Datenbank jeweils eine Kategorie
(``keyword_taetigkeitsbericht``) festgelegt ist und eine
Stundenanzahl (``n_sessions``). Die möglichen keywords sind beschrieben in
:doc:`Mögliche Tätigkeitsbericht-Kategorien <../taetigkeitsbericht_keywords>`.

Der Befehl ``edupsyadmin taetigkeitsbericht`` erlaubt die Erstellung eines
Tätigkeitsbericht unter der Angabe der Anzahl Anrechnungsstunden (im Beispiel
unten 3) und der Anzahl Schüler (im Beispiel unten 500 für die Schule mit dem
Kürzel ``schulkuerzela`` und 400 für die Schule mit dem Kürzel
``schulkuerzelb``).

.. code-block:: console

  $ edupsyadmin taetigkeitsbericht 3 schulkuerzela500 schulkuerzelb400

Dieser Befehl erstellt viele Dateien für den Tätigkeitsbericht, die dann in
einem PDF-Bericht zusammengefasst werden.

Das Beispiel oben geht davon aus, dass Vollzeit 23 Wochenstunden entspricht.
Über die Flag ``--wstd_total`` kann die Wochenstundenanzahl angepasst werden,
damit im Bericht korrekte Angaben gemacht werden zu den Zeitstunden, die den
angegebenen Anrechnungsstunden entsprechen.

.. code-block:: console

   $ edupsyadmin taetigkeitsbericht --wstd_total 28 3 schulkuerzela500 schulkuerzelb400
